using System;
using System.Collections.Generic;
using UnityEngine;

namespace FoldSpike
{
    // Mirrors data/garments.json. A copy lives in Assets/Resources so a build can load it;
    // the editor builder warns when the two diverge.
    [Serializable]
    public class FoldSpec
    {
        public string axis;   // "y" = vertical crease (mirror x), "x" = horizontal crease (mirror y)
        public float at;      // 0..1 along that axis
        public string dir;    // which flap moves: left/right (axis y), up/down (axis x)
    }

    [Serializable]
    public class Garment
    {
        public string id;
        public string name;
        public string category;
        public string fold_family;
        public FoldSpec[] folds;
        public int slots;
        public int difficulty;
        public string material;
        public int[] room_ids;
        public string codex;
    }

    [Serializable]
    public class GarmentDb
    {
        public int count;
        public Garment[] garments;
    }

    public static class GarmentLevel
    {
        // axis y -> vertical crease; dir names the flap that moves.
        // FoldMesh.CollectFlapIndices uses side*sideSign>0 with n = left normal of dir, so a
        // line drawn bottom->top has n=(-1,0): side>0 on the left. That makes "left" = +1.
        public static FoldLine ToLine(FoldSpec spec, double width, double height)
        {
            if (spec == null) return new FoldLine();
            double at = Math.Max(0.0, Math.Min(1.0, spec.at));
            if (spec.axis == "y")
            {
                double x = (at - 0.5) * width;
                return new FoldLine(new Vec2d(x, -height * 0.5), new Vec2d(x, height * 0.5));
            }
            double y = (at - 0.5) * height;
            return new FoldLine(new Vec2d(-width * 0.5, y), new Vec2d(width * 0.5, y));
        }

        public static int SideSign(FoldSpec spec)
        {
            if (spec == null) return 1;
            if (spec.axis == "y") return spec.dir == "right" ? -1 : 1;
            return spec.dir == "down" ? -1 : 1;
        }

        // Reference silhouette: fold a throwaway mesh through every spec, then take its hull.
        // This is the design target, and it is computed from the same rules the player must
        // satisfy - so comparing the player's hull to it is a real test, not a mirror.
        public static Vec2d[] TargetHull(Garment g, double width, double height)
        {
            FoldMesh refMesh = new FoldMesh(width, height);
            if (g != null && g.folds != null)
            {
                for (int i = 0; i < g.folds.Length; i++)
                {
                    FoldSpec s = g.folds[i];
                    FoldLine line = ToLine(s, width, height);
                    refMesh.Fold(line, 180.0, SideSign(s));
                }
            }
            return refMesh.GetHull(false);
        }

        public static GarmentDb Load()
        {
            TextAsset asset = Resources.Load<TextAsset>("garments");
            if (asset == null)
            {
                Debug.LogWarning("[FoldSpike] Resources/garments.json missing");
                return new GarmentDb { count = 0, garments = new Garment[0] };
            }
            GarmentDb db = JsonUtility.FromJson<GarmentDb>(asset.text);
            if (db == null || db.garments == null) return new GarmentDb { count = 0, garments = new Garment[0] };
            return db;
        }

        public static List<Garment> Room(int roomId, GarmentDb db, int take)
        {
            var list = new List<Garment>();
            if (db == null || db.garments == null) return list;
            for (int i = 0; i < db.garments.Length && list.Count < take; i++)
            {
                Garment g = db.garments[i];
                if (g.room_ids == null) continue;
                for (int k = 0; k < g.room_ids.Length; k++)
                {
                    if (g.room_ids[k] == roomId) { list.Add(g); break; }
                }
            }
            // Room may list fewer garments than a drawer holds; pad with the next items so the
            // loop always has a full drawer to fill.
            for (int i = 0; list.Count < take && i < db.garments.Length; i++)
            {
                if (!list.Contains(db.garments[i])) list.Add(db.garments[i]);
            }
            return list;
        }
    }
}
