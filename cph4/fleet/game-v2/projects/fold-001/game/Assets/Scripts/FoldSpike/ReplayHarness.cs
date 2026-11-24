using System;
using System.Collections.Generic;
using UnityEngine;

namespace FoldSpike
{
    // Determinism gate: replay the recorded fold sequence 20 times and require the same
    // quantised vertex hash and the same verdict every run. This is the number the spike
    // has to report before anyone trusts the judge.
    public sealed class ReplayHarness : MonoBehaviour
    {
        public FoldController Controller;
        public DrawerController Drawer;
        public int RepeatCount = 20;
        public bool RunOnStart = false;

        // Optional override; when empty the target is the left half of the paper. That default
        // alone cannot certify a fold (an unfolded sheet covers it too), which is why Run also
        // measures the unfolded and wrong-side controls.
        public Vector2[] TargetOutline;

        readonly CoverageJudge _judge = new CoverageJudge();

        public bool LastConsistent { get; private set; }
        public bool LastGateLive { get; private set; }
        public string LastReport { get; private set; }

        void Start()
        {
            if (RunOnStart) Run();
        }

        [ContextMenu("Run replay")]
        public void Run()
        {
            if (Controller == null || Controller.Paper == null)
            {
                LastConsistent = false;
                LastReport = "REPLAY: FoldController missing or not initialised";
                Debug.LogWarning("[FoldSpike] " + LastReport);
                return;
            }

            bool hasLiveReference = Controller.InputLog.Count > 0;
            List<InputEvent> log = hasLiveReference
                ? new List<InputEvent>(Controller.InputLog)
                : BuildDefaultLog();

            Vec2d[] target = ResolveTarget();

            // The live session's final state is the reference when a real drag produced the log;
            // a synthesised log has no live state, so run 0 becomes the reference instead.
            ulong liveHash = hasLiveReference ? Controller.CurrentHash() : 0UL;

            int runs = RepeatCount < 1 ? 1 : RepeatCount;
            double[] ms = new double[runs];
            bool consistent = true;

            ulong firstHash = 0UL;
            CoverageResult firstResult = new CoverageResult();
            string firstLabel = null;

            for (int r = 0; r < runs; r++)
            {
                System.Diagnostics.Stopwatch sw = System.Diagnostics.Stopwatch.StartNew();

                Controller.ResetForReplay();
                for (int i = 0; i < log.Count; i++) Controller.Replay(log[i]);
                CoverageResult res = _judge.Judge(Controller.Paper, target, false);

                sw.Stop();
                ms[r] = sw.Elapsed.TotalMilliseconds;

                ulong hash = Controller.CurrentHash();
                if (r == 0)
                {
                    firstHash = hash;
                    firstResult = res;
                    firstLabel = res.label;
                    if (hasLiveReference && hash != liveHash) consistent = false;
                }
                else if (hash != firstHash || res.label != firstLabel)
                {
                    consistent = false;
                }
            }

            Array.Sort(ms);
            double total = 0.0;
            for (int i = 0; i < ms.Length; i++) total += ms[i];
            double median = ms[ms.Length / 2];

            LastConsistent = consistent;
            NegativeControl nc = MeasureNegativeControls(target);
            LastGateLive = nc.live;
            LastReport = BuildReport(runs, hasLiveReference, log.Count, consistent,
                                     firstHash, firstResult, ms[0], median, ms[ms.Length - 1], total)
                         + "\n" + nc.report
                         + DrawerReport();

            Debug.Log("[FoldSpike] " + LastReport);
        }

        string BuildReport(int runs, bool hasLiveReference, int logLength, bool consistent,
                           ulong hash, CoverageResult result,
                           double minMs, double medianMs, double maxMs, double totalMs)
        {
            string text = "REPLAY " + runs + "x"
                          + "  log=" + logLength + (hasLiveReference ? " folds (live)" : " folds (synthesised)")
                          + "  consistent=" + (consistent ? "YES" : "NO")
                          + "\n  hash  = 0x" + hash.ToString("X16")
                          + "\n  shape = " + result.label
                          + "  cov=" + result.coverage.ToString("F4")
                          + "  iou=" + result.iou.ToString("F4")
                          + "  (" + result.coveredPixels + "/" + result.targetPixels
                          + ", paper=" + result.paperPixels + ")"
                          + "\n  ms    = " + minMs.ToString("F2") + " / " + medianMs.ToString("F2")
                          + " / " + maxMs.ToString("F2") + "  (min/p50/max)"
                          + "\n  total = " + totalMs.ToString("F1") + "ms";
            return text;
        }

        string DrawerReport()
        {
            if (Drawer == null) return string.Empty;

            Drawer.ResetDrawer();
            bool placedAll = true;
            for (int i = 0; i < DrawerController.SlotCount; i++) placedAll &= Drawer.TryPlace("spike_" + i);
            bool rejected = !Drawer.TryPlace("spike_overflow");

            int slot;
            string picked;
            bool pickedUp = Drawer.TryPickUpLast(out slot, out picked);
            bool refilled = Drawer.TryPlace("spike_refill");
            int occupied = Drawer.Occupied;
            Drawer.ResetDrawer();

            return "\n  drawer= placed6=" + placedAll + " rejected7=" + rejected
                   + " pickedUp=" + pickedUp + " refilled=" + refilled + " occ=" + occupied;
        }

        struct NegativeControl
        {
            public double foldedIou;
            public double unfoldedIou;
            public double unfoldedCov;
            public double wrongSideIou;
            public bool live;
            public string report;
        }

        // A gate nobody has tried to fool is not a gate. The half-fold goal is the left half of
        // the sheet, so an unfolded sheet covers that target completely: on the old one-sided
        // metric it scored the same 1.0000 as a correct fold. IoU separates the two states, and
        // this control proves the separation on every run instead of once in a review.
        NegativeControl MeasureNegativeControls(Vec2d[] target)
        {
            NegativeControl nc = new NegativeControl();

            FoldController c = Controller;
            if (c == null || c.Paper == null || c.Candidates.Count == 0)
            {
                nc.report = "  ctl   = SKIPPED (no paper or candidates)  live=NO";
                return nc;
            }

            Vec2d[] wrongSide = CoverageJudge.HalfRect(c.Paper.RestBounds, false);

            c.ResetForReplay();
            CoverageResult unfolded = _judge.Judge(c.Paper, target, false);

            FoldLine line = c.Candidates[0].ToFoldLine();
            int sideSign = SideOfRightHalf(line);
            c.Paper.Fold(line, 180.0, sideSign);
            CoverageResult folded = _judge.Judge(c.Paper, target, false);
            CoverageResult wrong = _judge.Judge(c.Paper, wrongSide, false);
            c.ResetForReplay();

            nc.foldedIou = folded.iou;
            nc.unfoldedIou = unfolded.iou;
            nc.unfoldedCov = unfolded.coverage;
            nc.wrongSideIou = wrong.iou;
            nc.live = folded.iou >= _judge.PassIou
                      && unfolded.iou < _judge.MinIou
                      && wrong.iou < _judge.MinIou
                      && nc.foldedIou - nc.unfoldedIou >= 0.20;

            nc.report = "  ctl   = folded_iou=" + nc.foldedIou.ToString("F4")
                        + "  unfolded_iou=" + nc.unfoldedIou.ToString("F4")
                        + "  unfolded_cov=" + nc.unfoldedCov.ToString("F4")
                        + "  wrongside_iou=" + nc.wrongSideIou.ToString("F4")
                        + "  live=" + (nc.live ? "YES" : "NO");
            return nc;
        }

        // One midline fold is enough to exercise mirror, layer, hash and coverage. A scene that
        // wants a richer trace just performs real folds first and lets the harness record them.
        List<InputEvent> BuildDefaultLog()
        {
            List<InputEvent> log = new List<InputEvent>();
            if (Controller.Candidates.Count == 0) return log;

            FoldLine line = Controller.Candidates[0].ToFoldLine();

            InputEvent e = new InputEvent();
            e.kind = InputKind.Fold;
            e.candidateIndex = 0;
            e.angleDeg = 180.0;
            e.sideSign = SideOfRightHalf(line);
            log.Add(e);
            return log;
        }

        // Probe the paper's right edge instead of assuming a normal direction, so the default
        // trace folds right-over-left whichever way the candidate endpoints were authored.
        int SideOfRightHalf(FoldLine line)
        {
            Bounds2D b = Controller.Paper.RestBounds;
            Vec2d probe = new Vec2d(b.Max.x * 0.5, b.Center.y);
            return line.SignedDistance(probe) > 0.0 ? 1 : -1;
        }

        Vec2d[] ResolveTarget()
        {
            if (TargetOutline != null && TargetOutline.Length >= 3)
            {
                Vec2d[] poly = new Vec2d[TargetOutline.Length];
                for (int i = 0; i < TargetOutline.Length; i++) poly[i] = Vec2d.From(TargetOutline[i]);
                return poly;
            }
            return CoverageJudge.HalfRect(Controller.Paper.RestBounds, true);
        }
    }
}
