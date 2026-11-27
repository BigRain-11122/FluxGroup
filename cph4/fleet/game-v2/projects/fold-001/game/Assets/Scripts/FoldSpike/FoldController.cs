using System;
using System.Collections.Generic;
using UnityEngine;

namespace FoldSpike
{
    public struct PointerFrame
    {
        public bool pressed;
        public bool held;
        public bool released;
        public Vector2 screen;
    }

    // One pointer abstraction for mouse/touch/pen (TECH-PLAN section 2). The spike's default
    // adapter reads legacy Input so the scene works with zero packages; the production router
    // swaps this implementation and nothing else in the controller changes.
    public interface IPointerSource
    {
        bool TryRead(out PointerFrame frame);
    }

    public sealed class LegacyPointerSource : IPointerSource
    {
        bool _wasDown;

        public bool TryRead(out PointerFrame frame)
        {
            bool down = Input.GetMouseButton(0);
            frame.screen = Input.mousePosition;
            frame.pressed = down && !_wasDown;
            frame.held = down && _wasDown;
            frame.released = !down && _wasDown;
            _wasDown = down;
            return true;
        }
    }

    // Candidates are Vector2 so they serialise in the Inspector; the double-precision
    // FoldLine is built on use.
    [Serializable]
    public struct CandidateFold
    {
        public Vector2 a;
        public Vector2 b;
        public bool isSolution;

        public FoldLine ToFoldLine()
        {
            return new FoldLine(Vec2d.From(a), Vec2d.From(b));
        }
    }

    public enum InputKind
    {
        Fold = 0,
        Undo = 1
    }

    // The log stores the settled fold (candidate, side, angle), not raw pointer frames:
    // this harness proves geometry determinism, not feel. Frame-level pointer replay would
    // need a fixed timestep and is deliberately out of scope.
    [Serializable]
    public struct InputEvent
    {
        public InputKind kind;
        public int candidateIndex;
        public double angleDeg;
        public int sideSign;
    }

    public sealed class FoldController : MonoBehaviour
    {
        public Camera Cam;
        public MeshFilter PaperMeshFilter;
        public float PaperWidth = 1.0f;
        public float PaperHeight = 1.0f;

        // 1 solution + 1-2 distractors (GAMEPLAY section 3). The solution must be index 0 for
        // ReplayHarness's synthesised log; ValidateCandidates warns otherwise.
        public List<CandidateFold> Candidates = new List<CandidateFold>();

        public float SnapScreenPercent = 0.03f;
        public float MinCommitAngle = 25.0f;
        public float SettleSeconds = 0.15f;
        public bool UseLegacyInput = true;

        public readonly List<InputEvent> InputLog = new List<InputEvent>();

        FoldMesh _paper;
        Mesh _mesh;
        IPointerSource _pointer;

        bool _dragging;
        bool _dragPending;
        Vector2 _pendingPress;
        int _dragCandidate = -1;
        FoldLine _dragLine;
        int _dragSide = 1;
        double _dragStartFlapDist;
        double _dragFlapWidth;
        double _dragAngle;

        bool _tweenActive;
        double _tweenFrom;
        double _tweenTo;
        bool _tweenCommits;
        float _tweenTime;

        public FoldMesh Paper { get { return _paper; } }
        public bool IsDragging { get { return _dragging; } }
        public int LastFoldCandidate { get; private set; }
        public double DragAngle { get { return _dragAngle; } }
        public int FoldCount { get { return _paper == null ? 0 : _paper.FoldCount; } }

        void Awake()
        {
            Initialize();
        }

        // Split from Awake so EditMode tests and ReplayHarness can build a controller without
        // entering Play mode.
        public void Initialize()
        {
            if (_paper != null) return;

            _paper = new FoldMesh(PaperWidth, PaperHeight);
            _pointer = new LegacyPointerSource();

            if (PaperMeshFilter != null)
            {
                _mesh = new Mesh();
                _mesh.name = "FoldPaper";
                PaperMeshFilter.mesh = _mesh;
                _paper.BuildUnityMesh(_mesh);
            }

            Render();
            ValidateCandidates();
        }

        void Update()
        {
            Tick(Time.deltaTime);
        }

        // dt is injected instead of read from Time so the settle tween is drivable from a test
        // and from the replay harness at a fixed step.
        public void Tick(float dt)
        {
            if (_tweenActive)
            {
                AdvanceTween(dt);
                return;
            }

            if (!UseLegacyInput || _pointer == null) return;

            PointerFrame frame;
            if (!_pointer.TryRead(out frame)) return;

            Vector2 world = ScreenToWorld(frame.screen);
            if (frame.pressed) BeginDrag(world);
            else if (frame.held) DragTo(world);
            else if (frame.released) EndDrag();
        }

        void ValidateCandidates()
        {
            int solutions = 0;
            for (int i = 0; i < Candidates.Count; i++) if (Candidates[i].isSolution) solutions++;
            int distractors = Candidates.Count - solutions;
            if (solutions != 1 || distractors < 1 || distractors > 2)
            {
                Debug.LogWarning("[FoldSpike] candidates should be 1 solution + 1-2 distractors, found "
                                 + solutions + "+" + distractors);
            }
        }

        // Creases cross at the middle of the sheet, so "nearest line to the press" picks the
        // wrong one exactly where players press. The drag direction decides instead: press is
        // remembered, and the first clear movement picks the crease it is perpendicular to.
        public bool BeginDrag(Vector2 world)
        {
            if (_paper == null || _paper.HasPreview) return false;

            Bounds2D bounds = _paper.RestBounds;
            Vec2d press = Vec2d.From(world);
            if (press.x < bounds.Min.x || press.x > bounds.Max.x ||
                press.y < bounds.Min.y || press.y > bounds.Max.y) return false;
            if (Candidates.Count == 0) return false;

            _dragPending = true;
            _pendingPress = world;
            _dragging = false;
            return true;
        }

        void ResolvePending(Vector2 world)
        {
            Vector2 mv = world - _pendingPress;
            if (mv.sqrMagnitude < 0.0004f) return;   // under 0.02 world: still deciding

            Vec2d dir = new Vec2d(mv.x, mv.y).Normalized;
            int best = -1;
            double bestScore = -1e9;
            for (int i = 0; i < Candidates.Count; i++)
            {
                FoldLine line = Candidates[i].ToFoldLine();
                if (!line.IsValid) continue;
                double align = Math.Abs(Vec2d.Dot(dir, line.Normal));
                if (align < 0.30) continue;           // not perpendicular enough to be this crease
                double dist = DistanceToSegment(_pendingPress, line);
                if (dist > 0.45) continue;            // too far from the press to intend it
                double score = align * 2.0 - dist;
                if (Candidates[i].isSolution) score += 0.05;
                if (score > bestScore) { bestScore = score; best = i; }
            }
            if (best < 0) { _dragPending = false; return; }

            _dragPending = false;
            StartDrag(best, _pendingPress);
        }

        void StartDrag(int best, Vector2 world)
        {
            FoldLine chosen = Candidates[best].ToFoldLine();
            double signed = chosen.SignedDistance(Vec2d.From(world));

            int side;
            if (Math.Abs(signed) < 1e-6)
            {
                // A press exactly on the crease has no side to read; folding the heavier half
                // beats aborting the gesture under the player's finger.
                double plus = _paper.MaxSignedDistance(chosen, 1);
                double minus = _paper.MaxSignedDistance(chosen, -1);
                if (plus < 1e-4 && minus < 1e-4) return;
                side = plus >= minus ? 1 : -1;
            }
            else
            {
                side = signed > 0.0 ? 1 : -1;
            }

            double flapWidth = _paper.MaxSignedDistance(chosen, side);
            if (flapWidth < 1e-4) return;

            // Grabbing on the crease itself would otherwise start at 0 travel and need a full
            // paper width of drag; treat it as a mid-flap grab instead.
            double startAbs = Math.Abs(signed);
            if (startAbs < flapWidth * 0.05) startAbs = flapWidth * 0.5;

            _dragging = true;
            _dragCandidate = best;
            _dragLine = chosen;
            _dragSide = side;
            _dragStartFlapDist = startAbs;
            _dragFlapWidth = flapWidth;
            _dragAngle = 0.0;
            _paper.BeginPreview(chosen, 0.0, side);
            Render();
            if (TraceFolds)
            {
                Debug.Log("[Fold] begin idx=" + best + " side=" + side
                          + " signed=" + signed.ToString("0.000")
                          + " startAbs=" + startAbs.ToString("0.000")
                          + " flap=" + flapWidth.ToString("0.000"));
            }
        }

        public bool TraceFolds = false;

        public void DragTo(Vector2 world)
        {
            if (_dragPending) { ResolvePending(world); if (_dragPending) return; }
            if (!_dragging) return;

            // Measured in the flap's own frame so a finger that starts mid-flap still maps
            // to a full 0-180 sweep instead of jumping to a half fold on press.
            double signed = _dragLine.SignedDistance(Vec2d.From(world)) * _dragSide;
            double travel = _dragStartFlapDist - signed;
            double span = 2.0 * Math.Max(_dragStartFlapDist, _dragFlapWidth * 0.2);
            double angle = Clamp01(travel / span) * 180.0;
            if (angle < 0.05) angle = 0.0;

            _dragAngle = angle;
            _paper.UpdatePreview(angle);
            Render();
        }

        public void EndDrag()
        {
            if (_dragPending) { _dragPending = false; return; }
            if (!_dragging) return;
            _dragging = false;

            // Below 25 degrees the paper has not committed, so it springs back; at or above
            // it the settle tween finishes the fold even if the finger stopped short.
            if (_dragAngle >= MinCommitAngle) StartTween(180.0, true);
            else StartTween(0.0, false);
        }

        public void CancelDrag()
        {
            _dragging = false;
            _dragPending = false;
            if (_paper != null) _paper.ClearPreview();
            _dragAngle = 0.0;
            Render();
        }

        void StartTween(double targetAngle, bool commits)
        {
            _tweenActive = true;
            _tweenFrom = _dragAngle;
            _tweenTo = targetAngle;
            _tweenCommits = commits;
            _tweenTime = 0f;
        }

        void AdvanceTween(float dt)
        {
            _tweenTime += dt;
            float k = SettleSeconds > 0f ? Mathf.Clamp01(_tweenTime / SettleSeconds) : 1f;
            double eased = k * k * (3.0 - 2.0 * k);

            _dragAngle = _tweenFrom + (_tweenTo - _tweenFrom) * eased;
            _paper.UpdatePreview(_dragAngle);
            Render();

            if (k < 1f) return;

            _tweenActive = false;
            if (_tweenCommits)
            {
                // Commit at the tween target, not at the raw release angle: the log then
                // holds exactly the geometry the player saw settle.
                CommitDrag(_tweenTo);
            }
            else
            {
                _paper.ClearPreview();
                _dragAngle = 0.0;
                _dragCandidate = -1;
                Render();
            }
        }

        void CommitDrag(double angleDeg)
        {
            FoldCommand cmd = _paper.Fold(_dragLine, angleDeg, _dragSide);
            _paper.ClearPreview();

            if (cmd != null)
            {
                // The game removes a used crease from Candidates; it needs to know which one.
                LastFoldCandidate = _dragCandidate;
                InputEvent e = new InputEvent();
                e.kind = InputKind.Fold;
                e.candidateIndex = _dragCandidate;
                e.angleDeg = angleDeg;
                e.sideSign = _dragSide;
                InputLog.Add(e);
            }

            _dragCandidate = -1;
            _dragAngle = 0.0;
            Render();
        }

        public bool Undo()
        {
            if (_paper == null || _paper.HasPreview) return false;
            if (!_paper.UndoLast()) return false;

            InputEvent e = new InputEvent();
            e.kind = InputKind.Undo;
            e.candidateIndex = -1;
            InputLog.Add(e);
            Render();
            return true;
        }

        public void ResetPaper()
        {
            _dragging = false;
            _dragPending = false;
            _tweenActive = false;
            _dragCandidate = -1;
            _dragAngle = 0.0;
            if (_paper != null) _paper.Reset();
            InputLog.Clear();
            Render();
        }

        // Replay path: no tween, no logging, same committed geometry.
        public bool Replay(InputEvent e)
        {
            if (_paper == null) return false;

            if (e.kind == InputKind.Undo) return _paper.UndoLast();

            if (e.candidateIndex < 0 || e.candidateIndex >= Candidates.Count) return false;
            FoldLine line = Candidates[e.candidateIndex].ToFoldLine();
            return _paper.Fold(line, e.angleDeg, e.sideSign) != null;
        }

        public void ResetForReplay()
        {
            _dragging = false;
            _dragPending = false;
            _tweenActive = false;
            _dragCandidate = -1;
            _dragAngle = 0.0;
            if (_paper != null) _paper.Reset();
            Render();
        }

        public ulong CurrentHash()
        {
            return _paper == null ? 0UL : _paper.ComputeHash();
        }

        public double SnapRadiusWorld()
        {
            if (Cam == null || !Cam.orthographic) return _paper != null ? _paper.Width * 0.05 : 0.05;
            double screenWidthWorld = Cam.orthographicSize * 2.0 * Cam.aspect;
            return screenWidthWorld * SnapScreenPercent;
        }

        Vector2 ScreenToWorld(Vector2 screen)
        {
            if (Cam == null) return screen;
            // The paper lives on z=0 and the ortho camera looks down +z, so the sampling
            // depth is simply its distance to that plane.
            float depth = Mathf.Abs(0f - Cam.transform.position.z);
            Vector3 w = Cam.ScreenToWorldPoint(new Vector3(screen.x, screen.y, depth));
            return new Vector2(w.x, w.y);
        }

        static double DistanceToSegment(Vector2 p, FoldLine line)
        {
            Vec2d v = Vec2d.From(p);
            Vec2d ab = line.b - line.a;
            double len2 = ab.x * ab.x + ab.y * ab.y;
            if (len2 < 1e-12) return (v - line.a).Length;
            double t = Vec2d.Dot(v - line.a, ab) / len2;
            if (t < 0.0) t = 0.0;
            if (t > 1.0) t = 1.0;
            Vec2d closest = line.a + ab * t;
            return (v - closest).Length;
        }

        static double Clamp01(double v)
        {
            if (v < 0.0) return 0.0;
            if (v > 1.0) return 1.0;
            return v;
        }

        void Render()
        {
            if (_mesh == null || _paper == null) return;
            _paper.ApplyToUnityMesh(_mesh, _paper.HasPreview);
        }

        // Redraw after geometry was changed from outside (benchmark pre-fold, scripted play).
        public void Refresh()
        {
            Render();
        }

        void OnDrawGizmos()
        {
            // Candidate lines are the only thing worth seeing before the paper renders; a
            // wrong line in the Inspector is the most common setup mistake.
            if (Candidates == null) return;
            for (int i = 0; i < Candidates.Count; i++)
            {
                Gizmos.color = Candidates[i].isSolution ? new Color(0.85f, 0.75f, 0.2f, 1f) : new Color(0.4f, 0.4f, 0.4f, 1f);
                Gizmos.DrawLine(new Vector3(Candidates[i].a.x, Candidates[i].a.y, 0f),
                                new Vector3(Candidates[i].b.x, Candidates[i].b.y, 0f));
            }
        }
    }
}
