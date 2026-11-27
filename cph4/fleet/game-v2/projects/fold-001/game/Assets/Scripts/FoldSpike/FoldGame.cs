using System;
using System.Collections.Generic;
using UnityEngine;

namespace FoldSpike
{
    // The playable loop: fold each garment to its target silhouette, then drop it into a drawer
    // slot. One session = one drawer (6 slots). No fail state: a wrong fold is undone, not lost.
    //
    // The pointer is owned here and forwarded to FoldController, so a scripted pointer can drive
    // the whole loop in tests and benchmarks without touching Input.
    public sealed class FoldGame : MonoBehaviour
    {
        public FoldController Controller;
        public DrawerController Drawer;
        public Camera Cam;
        public Transform PaperRoot;          // the GameObject carrying the paper mesh
        public int RoomId = 1;
        public int ItemsPerDrawer = 6;
        public float PlaceSnapRadius = 0.16f;
        public bool AutoLoad = true;

        public IPointerSource Pointer;
        public float JudgePassIou = 0.92f;

        enum Phase { Folding, Placing, Between, Complete }

        readonly List<Garment> _items = new List<Garment>();
        readonly List<Vec2d> _target = new List<Vec2d>();
        readonly CoverageJudge _judge = new CoverageJudge();
        readonly List<LineRenderer> _hints = new List<LineRenderer>();

        Phase _phase = Phase.Between;
        int _index = -1;
        int _foldsSeen;
        int _placed;
        float _itemStart;
        float _sessionStart;
        float _lastIou;
        bool _placing;
        Vector2 _placeStart;
        Vector3 _paperHome;
        LineRenderer _ghost;
        Material _lineMat;

        public float ItemSeconds { get { return Mathf.Max(0f, Time.time - _itemStart); } }
        public float SessionSeconds { get { return Mathf.Max(0f, Time.time - _sessionStart); } }
        public int Placed { get { return _placed; } }
        public int Total { get { return _items.Count; } }
        public float LastIou { get { return _lastIou; } }
        public string CurrentItem { get { return _index >= 0 && _index < _items.Count ? _items[_index].name : ""; } }
        public bool IsComplete { get { return _phase == Phase.Complete; } }

        // Accessors for the automated playtest and benchmark; they expose state, not controls.
        public Garment CurrentGarment { get { return _index >= 0 && _index < _items.Count ? _items[_index] : null; } }
        public int FoldsDone { get { return Controller != null ? Controller.FoldCount : 0; } }
        public double PaperWidth { get { return Controller != null ? Controller.PaperWidth : 1.0; } }
        public double PaperHeight { get { return Controller != null ? Controller.PaperHeight : 0.7; } }
        public FoldMesh Paper { get { return Controller != null ? Controller.Paper : null; } }
        public bool AwaitingFold { get { return _phase == Phase.Folding; } }
        public bool AwaitingPlacement { get { return _phase == Phase.Placing; } }
        public string PhaseName { get { return _phase.ToString(); } }

        public int FirstFreeSlot()
        {
            if (Drawer == null) return -1;
            for (int i = 0; i < DrawerController.SlotCount; i++)
            {
                if (!Drawer.IsSlotOccupied(i)) return i;
            }
            return -1;
        }

        public Vector3 SlotWorld(int slot)
        {
            return Drawer != null ? Drawer.SlotWorldPosition(slot) : Vector3.zero;
        }

        void Start()
        {
            if (AutoLoad) BeginRoom();
        }

        public void BeginRoom()
        {
            if (Controller == null || Controller.Paper == null) Controller = GetComponent<FoldController>();
            if (Controller == null) { Debug.LogError("[FoldSpike] FoldGame needs a FoldController"); enabled = false; return; }
            if (Pointer == null) Pointer = new LegacyPointerSource();

            Controller.UseLegacyInput = false;   // the game owns the pointer from here on
            _paperHome = PaperRoot != null ? PaperRoot.position : Vector3.zero;

            var db = GarmentLevel.Load();
            _items.Clear();
            _items.AddRange(GarmentLevel.Room(RoomId, db, Mathf.Max(1, ItemsPerDrawer)));
            Debug.Log("[FoldGame] room=" + RoomId + " items=" + _items.Count
                      + " garments_in_db=" + (db != null && db.garments != null ? db.garments.Length : -1));
            if (_items.Count == 0) { Debug.LogError("[FoldSpike] no garments loaded"); enabled = false; return; }

            if (Drawer != null) Drawer.ResetDrawer();
            _placed = 0;
            _index = 0;
            _sessionStart = Time.time;
            BuildHudLines();
            LoadItem(_items[0]);
        }

        void BuildHudLines()
        {
            _lineMat = new Material(Shader.Find("Sprites/Default"));
            _ghost = NewLine("TargetOutline", new Color(0.55f, 0.75f, 0.95f, 0.55f), 0.004f);
        }

        LineRenderer NewLine(string name, Color color, float width)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(transform, false);
            LineRenderer lr = go.AddComponent<LineRenderer>();
            lr.material = _lineMat;
            lr.useWorldSpace = false;
            lr.loop = true;
            lr.widthMultiplier = width;
            lr.startColor = color;
            lr.endColor = color;
            lr.positionCount = 0;
            lr.sortingOrder = 1;
            return lr;
        }

        void LoadItem(Garment g)
        {
            Controller.ResetPaper();
            if (PaperRoot != null) PaperRoot.position = _paperHome;

            // Candidates are the garment's own creases; the player may fold them in any order.
            Controller.Candidates = new List<CandidateFold>();
            _target.Clear();
            if (g != null && g.folds != null)
            {
                for (int i = 0; i < g.folds.Length; i++)
                {
                    FoldSpec s = g.folds[i];
                    FoldLine line = GarmentLevel.ToLine(s, Controller.PaperWidth, Controller.PaperHeight);
                    CandidateFold c = new CandidateFold();
                    c.a = line.a.ToVector2();
                    c.b = line.b.ToVector2();
                    c.isSolution = true;
                    Controller.Candidates.Add(c);
                }
            }

            Vec2d[] hull = GarmentLevel.TargetHull(g, Controller.PaperWidth, Controller.PaperHeight);
            if (hull != null)
            {
                for (int i = 0; i < hull.Length; i++) _target.Add(hull[i]);
            }
            Debug.Log("[FoldGame] item=" + (g != null ? g.id : "null") + " folds=" + (g != null && g.folds != null ? g.folds.Length : 0)
                      + " target_points=" + _target.Count + " candidates=" + Controller.Candidates.Count);
            ShowGhost(_target, _ghost);
            RefreshHints(g, 0);

            _lastIou = 0f;
            _foldsSeen = 0;
            _phase = Phase.Folding;
            _itemStart = Time.time;
        }

        void ShowGhost(List<Vec2d> hull, LineRenderer lr)
        {
            if (lr == null) return;
            if (hull == null || hull.Count < 3) { lr.positionCount = 0; return; }
            lr.positionCount = hull.Count;
            for (int i = 0; i < hull.Count; i++)
            {
                lr.SetPosition(i, new Vector3((float)hull[i].x, (float)hull[i].y, 0.02f));
            }
        }

        // Hints show the creases still available; they are rebuilt after every commit.
        void RefreshHints(Garment g, int fromFold)
        {
            for (int i = 0; i < _hints.Count; i++)
            {
                if (_hints[i] != null) Destroy(_hints[i].gameObject);
            }
            _hints.Clear();
            if (g == null || g.folds == null) return;
            for (int i = fromFold; i < g.folds.Length; i++)
            {
                FoldLine line = GarmentLevel.ToLine(g.folds[i], Controller.PaperWidth, Controller.PaperHeight);
                LineRenderer lr = NewLine("Hint" + i, new Color(0.95f, 0.78f, 0.35f, 0.8f), 0.0035f);
                lr.loop = false;
                lr.positionCount = 2;
                lr.SetPosition(0, new Vector3((float)line.a.x, (float)line.a.y, 0.01f));
                lr.SetPosition(1, new Vector3((float)line.b.x, (float)line.b.y, 0.01f));
                _hints.Add(lr);
            }
        }

        void Update()
        {
            if (Controller == null || Controller.Paper == null) return;

            // A fold commits inside the settle tween, one to a few frames AFTER the release -
            // by then the pointer has no frames left. Detect the commit before touching the
            // pointer, otherwise it is only seen on the next gesture (or never).
            if (_phase == Phase.Folding && Controller.FoldCount != _foldsSeen)
            {
                _foldsSeen = Controller.FoldCount;
                OnFoldCommitted();
            }

            if (Pointer == null) return;

            PointerFrame f;
            if (!Pointer.TryRead(out f)) return;
            Vector2 world = ScreenToWorld(f.screen);

            if (_phase == Phase.Folding)
            {
                if (f.pressed)
                {
                    bool grabbed = Controller.BeginDrag(world);
                    Debug.Log("[FoldGame] press=" + world.ToString("0.000") + " grabbed=" + grabbed
                              + " candidates=" + Controller.Candidates.Count);
                }
                else if (f.held) Controller.DragTo(world);
                else if (f.released)
                {
                    Debug.Log("[FoldGame] release=" + world.ToString("0.000")
                              + " angle=" + Controller.DragAngle.ToString("0.0"));
                    Controller.EndDrag();
                }
                return;
            }

            if (_phase == Phase.Placing)
            {
                if (f.pressed)
                {
                    _placing = true;
                    _placeStart = world;
                }
                else if (f.held && _placing)
                {
                    Vector2 d = world - _placeStart;
                    if (PaperRoot != null) PaperRoot.position = _paperHome + new Vector3(d.x, d.y, 0f);
                }
                else if (f.released && _placing)
                {
                    _placing = false;
                    TryPlace(world);
                }
            }
        }

        void OnFoldCommitted()
        {
            _lastIou = JudgeNow();

            // A used crease must leave the candidate list, otherwise the next press snaps back
            // onto it and folds the same line twice.
            int used = Controller.LastFoldCandidate;
            if (used >= 0 && used < Controller.Candidates.Count)
            {
                Controller.Candidates.RemoveAt(used);
            }

            if (_lastIou >= JudgePassIou)
            {
                _phase = Phase.Placing;
                ClearHints();
            }
            else
            {
                // Keep going: more folds may still reach the target. Hints stay visible.
                RefreshHints(_items[_index], Controller.FoldCount);
            }
        }

        float JudgeNow()
        {
            Debug.Log("[Judge] call target_points=" + _target.Count
                      + " paper=" + (Controller != null && Controller.Paper != null));
            if (_target.Count < 3) return 0f;
            CoverageResult r = _judge.Judge(Controller.Paper, _target.ToArray(), false);
            if (Controller != null && Controller.TraceFolds)
            {
                Debug.Log("[Judge] covered=" + r.coveredPixels + " target=" + r.targetPixels
                          + " paper=" + r.paperPixels + " cov=" + r.coverage.ToString("0.000")
                          + " iou=" + r.iou.ToString("0.000"));
            }
            return (float)r.iou;
        }

        void ClearHints()
        {
            for (int i = 0; i < _hints.Count; i++) if (_hints[i] != null) Destroy(_hints[i].gameObject);
            _hints.Clear();
        }

        void TryPlace(Vector2 world)
        {
            if (Drawer == null) { PaperRoot.position = _paperHome; return; }
            int slot = NearestFreeSlot(world);
            if (slot < 0) { PaperRoot.position = _paperHome; return; }

            if (!Drawer.TryPlace(_items[_index].id))
            {
                PaperRoot.position = _paperHome;
                return;
            }

            Vector3 p = Drawer.SlotWorldPosition(slot);
            if (PaperRoot != null) PaperRoot.position = new Vector3(p.x, p.y, _paperHome.z);

            Debug.Log("[Item] id=" + _items[_index].id + " name=" + _items[_index].name
                      + " t=" + ItemSeconds.ToString("0.00") + "s"
                      + " folds=" + Controller.FoldCount
                      + " iou=" + _lastIou.ToString("0.000")
                      + " slot=" + slot);

            _placed++;
            _index++;
            if (_index >= _items.Count)
            {
                _phase = Phase.Complete;
                ClearHints();
                return;
            }
            _phase = Phase.Between;
            Invoke("NextItem", 0.25f);
        }

        void NextItem()
        {
            if (_phase != Phase.Between) return;
            LoadItem(_items[_index]);
        }

        int NearestFreeSlot(Vector2 world)
        {
            int best = -1;
            float bestD = PlaceSnapRadius;
            for (int i = 0; i < DrawerController.SlotCount; i++)
            {
                if (Drawer.IsSlotOccupied(i)) continue;
                Vector3 p = Drawer.SlotWorldPosition(i);
                float d = Vector2.Distance(world, new Vector2(p.x, p.y));
                if (d < bestD) { bestD = d; best = i; }
            }
            return best;
        }

        Vector2 ScreenToWorld(Vector2 screen)
        {
            if (Cam == null) return screen;
            float depth = Mathf.Abs(0f - Cam.transform.position.z);
            Vector3 w = Cam.ScreenToWorldPoint(new Vector3(screen.x, screen.y, depth));
            return new Vector2(w.x, w.y);
        }

        public bool Undo()
        {
            if (Controller == null || _phase == Phase.Complete) return false;
            bool ok = Controller.Undo();
            if (ok)
            {
                _phase = Phase.Folding;
                if (_index >= 0 && _index < _items.Count) RefreshHints(_items[_index], Controller.FoldCount);
            }
            return ok;
        }

        // Benchmark hook: put the sheet into its fully folded, max-layer state without animation,
        // so the frame numbers describe the worst case rather than a flat sheet.
        public void PreFoldForBench()
        {
            if (Controller == null || Controller.Paper == null) return;
            Garment g = CurrentGarment;
            if (g == null || g.folds == null) return;
            Controller.ResetPaper();
            for (int i = 0; i < g.folds.Length; i++)
            {
                Controller.Paper.Fold(GarmentLevel.ToLine(g.folds[i], Controller.PaperWidth, Controller.PaperHeight),
                                      180.0, GarmentLevel.SideSign(g.folds[i]));
            }
            Controller.Refresh();
            ClearHints();
        }

        void OnGUI()
        {
            GUIStyle big = new GUIStyle(GUI.skin.label);
            big.fontSize = 20;
            GUIStyle small = new GUIStyle(GUI.skin.label);
            small.fontSize = 14;

            GUI.Label(new Rect(16, 12, 720, 28),
                "Room " + RoomId + "   slot " + Mathf.Min(_placed + 1, Total) + "/" + Total +
                "   " + CurrentItem + "   item " + ItemSeconds.ToString("0.0") + "s" +
                "   session " + SessionSeconds.ToString("0.0") + "s", big);

            string hint;
            if (_phase == Phase.Folding) hint = "Drag along a yellow crease.  U = undo";
            else if (_phase == Phase.Placing) hint = "Shape matched (" + _lastIou.ToString("0.00") + ") - drag into a drawer slot";
            else if (_phase == Phase.Complete) hint = "Drawer complete in " + SessionSeconds.ToString("0.0") + "s";
            else hint = "Next garment...";
            GUI.Label(new Rect(16, 40, 900, 24), hint, small);

            if (_phase != Phase.Complete)
            {
                GUI.Label(new Rect(16, 62, 900, 24),
                    "folds " + Controller.FoldCount + "   iou " + _lastIou.ToString("0.000"), small);
            }
        }
    }
}
