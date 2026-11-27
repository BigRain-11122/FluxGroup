using System;
using System.Collections;
using System.Collections.Generic;
using Unity.Profiling;
using UnityEngine;

namespace FoldSpike
{
    // Deterministic pointer: a queued list of frames, one consumed per TryRead. Screen space,
    // because that is what the game converts from - the same path a mouse takes.
    public sealed class ScriptedPointer : IPointerSource
    {
        struct Frame { public Vector2 screen; public bool pressed, held, released; }

        readonly List<Frame> _frames = new List<Frame>();
        int _cursor;
        Camera _cam;

        public ScriptedPointer(Camera cam) { _cam = cam; }

        public bool Idle { get { return _cursor >= _frames.Count; } }

        Vector2 ToScreen(Vector2 world)
        {
            if (_cam == null) return world;
            Vector3 s = _cam.WorldToScreenPoint(new Vector3(world.x, world.y, 0f));
            return new Vector2(s.x, s.y);
        }

        public void Press(Vector2 world, int holdFrames = 1)
        {
            Vector2 s = ToScreen(world);
            _frames.Add(new Frame { screen = s, pressed = true });
            for (int i = 0; i < holdFrames; i++) _frames.Add(new Frame { screen = s, held = true });
        }

        public void MoveTo(Vector2 world, int frames = 6)
        {
            Vector2 to = ToScreen(world);
            Vector2 from = _frames.Count > 0 ? _frames[_frames.Count - 1].screen : to;
            int n = Mathf.Max(1, frames);
            for (int i = 1; i <= n; i++)
            {
                Vector2 s = Vector2.Lerp(from, to, (float)i / n);
                _frames.Add(new Frame { screen = s, held = true });
            }
        }

        public void Release(Vector2 world)
        {
            _frames.Add(new Frame { screen = ToScreen(world), released = true });
        }

        public void Clear() { _frames.Clear(); _cursor = 0; }

        public bool TryRead(out PointerFrame frame)
        {
            frame = new PointerFrame();
            if (_cursor >= _frames.Count) return false;
            Frame f = _frames[_cursor++];
            frame.screen = f.screen;
            frame.pressed = f.pressed;
            frame.held = f.held;
            frame.released = f.released;
            return true;
        }
    }

    // Drives a whole drawer with synthetic drags. This is the automated playtest: it proves the
    // loop closes, and it produces per-item timings that no hand-play could reproduce exactly.
    public sealed class AutoPlay : MonoBehaviour
    {
        public FoldGame Game;
        public int MaxItems = 0;          // 0 = whole drawer
        public bool QuitWhenDone = false;
        public bool Active = true;

        ScriptedPointer _pointer;
        int _started;

        void Start()
        {
            if (!Active) return;
            if (Game == null) Game = GetComponent<FoldGame>();
            _pointer = new ScriptedPointer(Game != null ? Game.Cam : Camera.main);
            if (Game != null) Game.Pointer = _pointer;
            _started = 0;
            StartCoroutine(Drive());
        }

        IEnumerator Drive()
        {
            yield return null;
            float lastProgress = Time.time;
            while (Game != null && !Game.IsComplete && (MaxItems <= 0 || _started < MaxItems))
            {
                Garment g = Game.CurrentGarment;
                if (g == null) { yield return null; continue; }

                int progressBefore = Game.Placed * 10 + Game.FoldsDone;

                // Fold every crease of this garment, one drag each.
                if (Game.AwaitingFold && g.folds != null)
                {
                    for (int i = Game.FoldsDone; i < g.folds.Length && Game.AwaitingFold; i++)
                    {
                        FoldSpec s = g.folds[i];
                        FoldLine line = GarmentLevel.ToLine(s, Game.PaperWidth, Game.PaperHeight);
                        int side = GarmentLevel.SideSign(s);
                        Vec2d n = line.Normal;
                        Vec2d mid = (line.a + line.b) * 0.5;
                        double flap = Game.Paper.MaxSignedDistance(line, side);
                        if (flap < 1e-4)
                        {
                            Debug.Log("[AutoPlay] skip fold " + i + " flap too small");
                            continue;
                        }

                        Vec2d grab = mid + n * (flap * 0.5 * side);
                        Vec2d drop = mid - n * (flap * 0.5 * side);

                        _pointer.Clear();
                        _pointer.Press(grab.ToVector2(), 2);
                        _pointer.MoveTo(drop.ToVector2(), 8);
                        _pointer.Release(drop.ToVector2());

                        int before = Game.FoldsDone;
                        float t0 = Time.time;
                        while (Time.time - t0 < 2.0f && Game.FoldsDone == before && !Game.AwaitingPlacement)
                        {
                            yield return null;
                        }
                        Debug.Log("[AutoPlay] fold " + i + " " + s.axis + "@" + s.at + " " + s.dir
                                  + " flap=" + flap.ToString("0.000")
                                  + " before=" + before + " after=" + Game.FoldsDone
                                  + " iou=" + Game.LastIou.ToString("0.000"));
                        yield return null;
                    }
                }

                // Then drop it into a free slot.
                if (Game.AwaitingPlacement)
                {
                    int slot = Game.FirstFreeSlot();
                    if (slot >= 0)
                    {
                        Vector3 p = Game.SlotWorld(slot);
                        _pointer.Clear();
                        _pointer.Press(new Vector2(0f, 0f), 2);
                        _pointer.MoveTo(new Vector2(p.x, p.y), 10);
                        _pointer.Release(new Vector2(p.x, p.y));

                        int beforePlaced = Game.Placed;
                        float t1 = Time.time;
                        while (Time.time - t1 < 3.0f && Game.Placed == beforePlaced) yield return null;
                        Debug.Log("[AutoPlay] place slot=" + slot + " placed=" + Game.Placed);
                        _started++;
                    }
                }

                if (Game.Placed * 10 + Game.FoldsDone != progressBefore) lastProgress = Time.time;
                // Frame counts are useless here: the loop can run thousands of frames per
                // second, so a 0.25 s next-item delay would look like a stall. Judge by time.
                if (Time.time - lastProgress > 6f)
                {
                    Debug.LogError("[AutoPlay] stalled: placed=" + Game.Placed + "/" + Game.Total
                                   + " folds=" + Game.FoldsDone + " phase=" + Game.PhaseName);
                    break;
                }
                yield return null;
            }

            if (Game != null) Debug.Log("[AutoPlay] done placed=" + Game.Placed + "/" + Game.Total
                                        + " session=" + Game.SessionSeconds.ToString("0.0") + "s");
            if (QuitWhenDone)
            {
                yield return new WaitForSeconds(0.5f);
                Application.Quit();
            }
        }
    }

    // Render + loop benchmark. Quits by itself and writes one JSON line per build, so a numbers
    // file cannot be confused with a hand-copied claim.
    public sealed class BenchmarkMode : MonoBehaviour
    {
        public FoldGame Game;
        public int Frames = 600;
        public int Warmup = 60;
        public string OutPath = "bench.json";

        IEnumerator Start()
        {
            // Vsync would pin every sample to the refresh rate and hide the real cost.
            QualitySettings.vSyncCount = 0;
            Application.targetFrameRate = -1;
            yield return null;

            Recorder drawCalls = Recorder.Start("Draw Calls Count");
            List<float> frames = new List<float>(Frames);
            yield return null;
            for (int i = 0; i < Warmup; i++) yield return null;

            float t0 = Time.realtimeSinceStartup;
            for (int i = 0; i < Frames; i++)
            {
                yield return null;
                frames.Add(Time.unscaledDeltaTime);
            }
            float elapsed = Time.realtimeSinceStartup - t0;

            frames.Sort();
            float p1 = frames[Mathf.Clamp(Mathf.CeilToInt(frames.Count * 0.01f) - 1, 0, frames.Count - 1)];
            float p50 = frames[frames.Count / 2];
            float p99 = frames[Mathf.Clamp(Mathf.FloorToInt(frames.Count * 0.99f), 0, frames.Count - 1)];
            float sum = 0f;
            for (int i = 0; i < frames.Count; i++) sum += frames[i];

            var sb = new System.Text.StringBuilder(256);
            sb.Append("{\"frames\":").Append(Frames)
              .Append(",\"elapsed_s\":").Append(elapsed.ToString("0.00"))
              .Append(",\"fps_avg\":").Append((Frames / Mathf.Max(elapsed, 1e-6f)).ToString("0.0"))
              .Append(",\"fps_p1low\":").Append((1f / Mathf.Max(p99, 1e-6f)).ToString("0.0"))
              .Append(",\"frame_ms_p50\":").Append((p50 * 1000f).ToString("0.00"))
              .Append(",\"frame_ms_p99\":").Append((p99 * 1000f).ToString("0.00"))
              .Append(",\"draw_calls_p50\":").Append(drawCalls.Value)
              .Append(",\"screen\":\"").Append(Screen.width).Append("x").Append(Screen.height).Append("\"")
              .Append(",\"placed\":").Append(Game != null ? Game.Placed : -1)
              .Append(",\"session_s\":").Append(Game != null ? Game.SessionSeconds.ToString("0.0") : "-1")
              .Append("}");
            drawCalls.Dispose();

            System.IO.File.WriteAllText(OutPath, sb.ToString() + "\n");
            Debug.Log("[Bench] " + sb);
            yield return null;
            Application.Quit();
        }

        struct Recorder
        {
            ProfilerRecorder _r;
            public static Recorder Start(string name)
            {
                Recorder rec = new Recorder();
                rec._r = ProfilerRecorder.StartNew(ProfilerCategory.Render, name, 1);
                return rec;
            }
            public long Value { get { return _r.Valid ? _r.LastValue : -1; } }
            public void Dispose() { if (_r.Valid) _r.Dispose(); }
        }
    }
}
