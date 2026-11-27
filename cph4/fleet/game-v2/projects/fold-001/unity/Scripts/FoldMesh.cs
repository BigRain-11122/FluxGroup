using System;
using System.Collections.Generic;
using UnityEngine;

namespace FoldSpike
{
    // Geometry is double everywhere: replay must be bit-stable across 20 runs, and float
    // accumulations drift enough to flip a 1.5px gold verdict on the last fold.
    public struct Vec2d
    {
        public double x;
        public double y;

        public Vec2d(double x, double y)
        {
            this.x = x;
            this.y = y;
        }

        public static Vec2d operator +(Vec2d a, Vec2d b) { return new Vec2d(a.x + b.x, a.y + b.y); }
        public static Vec2d operator -(Vec2d a, Vec2d b) { return new Vec2d(a.x - b.x, a.y - b.y); }
        public static Vec2d operator *(Vec2d a, double k) { return new Vec2d(a.x * k, a.y * k); }

        public static double Dot(Vec2d a, Vec2d b) { return a.x * b.x + a.y * b.y; }

        public static double Cross(Vec2d a, Vec2d b) { return a.x * b.y - a.y * b.x; }

        public double Length { get { return Math.Sqrt(x * x + y * y); } }

        public Vec2d Normalized
        {
            get
            {
                double len = Length;
                return len < 1e-12 ? new Vec2d(0.0, 0.0) : new Vec2d(x / len, y / len);
            }
        }

        public Vector2 ToVector2() { return new Vector2((float)x, (float)y); }

        public static Vec2d From(Vector2 v) { return new Vec2d(v.x, v.y); }

        public override string ToString()
        {
            return "(" + x.ToString("F5") + ", " + y.ToString("F5") + ")";
        }
    }

    public struct Vec3d
    {
        public double x;
        public double y;
        public double z;

        public Vec3d(double x, double y, double z)
        {
            this.x = x;
            this.y = y;
            this.z = z;
        }
    }

    public struct Bounds2D
    {
        public Vec2d Min;
        public Vec2d Max;

        public double Width { get { return Max.x - Min.x; } }
        public double Height { get { return Max.y - Min.y; } }
        public Vec2d Center { get { return new Vec2d((Min.x + Max.x) * 0.5, (Min.y + Max.y) * 0.5); } }

        public override string ToString()
        {
            return "[" + Min.ToString() + " .. " + Max.ToString() + "]";
        }
    }

    // A crease is the mirror axis. Both endpoints are in paper-local space, so a level
    // file can ship them as plain numbers without depending on any transform.
    public struct FoldLine
    {
        public Vec2d a;
        public Vec2d b;

        public FoldLine(Vec2d a, Vec2d b)
        {
            this.a = a;
            this.b = b;
        }

        public Vec2d Dir { get { return (b - a).Normalized; } }

        // Left-hand normal of Dir. Keeping one fixed convention is what makes the
        // signed-distance side test agree with the renderer for every candidate line.
        public Vec2d Normal
        {
            get
            {
                Vec2d d = Dir;
                return new Vec2d(-d.y, d.x);
            }
        }

        public double Length { get { return (b - a).Length; } }

        public bool IsValid { get { return Length > 1e-4; } }

        public double SignedDistance(Vec2d p)
        {
            Vec2d n = Normal;
            return Vec2d.Dot(p - a, n);
        }

        public Vec2d Project(Vec2d p)
        {
            Vec2d d = Dir;
            return a + d * Vec2d.Dot(p - a, d);
        }

        public FoldLine Reversed() { return new FoldLine(b, a); }
    }

    public sealed class FoldCommand
    {
        public FoldLine line;
        public double angleDeg;
        public int sideSign;
        public int[] indices;
        public Vec3d[] prevPos;
        public int[] prevLayer;
    }

    // Authoritative paper: 32x32 cells (33x33 = 1089 vertices, 2048 triangles) per TECH-PLAN 1.
    // The Unity Mesh is only a render copy; every judged number comes from this class.
    public sealed class FoldMesh
    {
        public const int Cells = 32;
        public const int VertsPerSide = Cells + 1;
        public const int VertexCount = VertsPerSide * VertsPerSide;
        public const int TriangleCount = Cells * Cells * 2;
        public const int MaxLayer = 5;

        // 2mm at a 1m paper: enough to beat z-fighting at 1080p, small enough that the
        // silhouette still reads as one sheet when the camera is straight down.
        public const double LayerGap = 0.002;

        const double FlapEpsilon = 1e-9;
        const double MinFoldAngle = 1e-3;

        readonly double _width;
        readonly double _height;
        readonly Vec3d[] _pos;
        readonly int[] _layer;
        readonly Vec3d[] _previewPos;
        readonly int[] _previewLayer;
        readonly int[] _tri;
        readonly Vector2[] _uv;
        readonly Vector3[] _renderVerts;
        readonly Color32[] _renderColors;
        readonly List<FoldCommand> _undo = new List<FoldCommand>();
        readonly Bounds2D _restBounds;

        FoldLine _previewLine;
        int _previewSide;
        int[] _previewIdx;
        bool _hasPreview;
        double _previewAngleDeg;

        public FoldMesh(double width, double height)
        {
            _width = width > 1e-6 ? width : 1.0;
            _height = height > 1e-6 ? height : 1.0;

            _pos = new Vec3d[VertexCount];
            _layer = new int[VertexCount];
            _previewPos = new Vec3d[VertexCount];
            _previewLayer = new int[VertexCount];
            _renderVerts = new Vector3[VertexCount];
            _renderColors = new Color32[VertexCount];
            _uv = new Vector2[VertexCount];
            _tri = new int[TriangleCount * 3];

            for (int y = 0; y < VertsPerSide; y++)
            {
                for (int x = 0; x < VertsPerSide; x++)
                {
                    int i = y * VertsPerSide + x;
                    double px = ((double)x / Cells - 0.5) * _width;
                    double py = ((double)y / Cells - 0.5) * _height;
                    _pos[i] = new Vec3d(px, py, 0.0);
                    _previewPos[i] = _pos[i];
                    _uv[i] = new Vector2((float)x / Cells, (float)y / Cells);
                }
            }

            int t = 0;
            for (int y = 0; y < Cells; y++)
            {
                for (int x = 0; x < Cells; x++)
                {
                    int i0 = y * VertsPerSide + x;
                    int i1 = i0 + 1;
                    int i2 = i0 + VertsPerSide + 1;
                    int i3 = i0 + VertsPerSide;
                    // Unity front faces are clockwise seen from the camera; a 2D camera sits on -z.
                    _tri[t++] = i0; _tri[t++] = i3; _tri[t++] = i1;
                    _tri[t++] = i3; _tri[t++] = i2; _tri[t++] = i1;
                }
            }

            _restBounds = new Bounds2D();
            _restBounds.Min = new Vec2d(-_width * 0.5, -_height * 0.5);
            _restBounds.Max = new Vec2d(_width * 0.5, _height * 0.5);
        }

        public double Width { get { return _width; } }
        public double Height { get { return _height; } }
        public Bounds2D RestBounds { get { return _restBounds; } }
        public int FoldCount { get { return _undo.Count; } }
        public bool CanUndo { get { return _undo.Count > 0; } }
        public bool HasPreview { get { return _hasPreview; } }
        public double PreviewAngleDeg { get { return _previewAngleDeg; } }
        public int[] TriangleIndices { get { return _tri; } }

        public int LayerAt(int vertex)
        {
            return _layer[vertex];
        }

        public void Reset()
        {
            _undo.Clear();
            _hasPreview = false;
            _previewIdx = null;
            for (int y = 0; y < VertsPerSide; y++)
            {
                for (int x = 0; x < VertsPerSide; x++)
                {
                    int i = y * VertsPerSide + x;
                    double px = ((double)x / Cells - 0.5) * _width;
                    double py = ((double)y / Cells - 0.5) * _height;
                    _pos[i] = new Vec3d(px, py, 0.0);
                    _previewPos[i] = _pos[i];
                    _layer[i] = 0;
                    _previewLayer[i] = 0;
                }
            }
        }

        // Mirror axis rotation: the flap swings out of plane by |s|*sin(theta) and lands at
        // -s at 180 degrees, which is the same picture as a pure mirror but gives the drag
        // preview its cosine foreshortening for free.
        static Vec3d RotateAboutLine(Vec3d p, Vec2d origin, Vec2d dir, Vec2d nrm, double cos, double sin)
        {
            double vx = p.x - origin.x;
            double vy = p.y - origin.y;
            double along = vx * dir.x + vy * dir.y;
            double side = vx * nrm.x + vy * nrm.y;
            double newSide = cos * side;
            double newZ = p.z + sin * Math.Abs(side);
            return new Vec3d(
                origin.x + dir.x * along + nrm.x * newSide,
                origin.y + dir.y * along + nrm.y * newSide,
                newZ);
        }

        int[] CollectFlapIndices(FoldLine line, int sideSign)
        {
            Vec2d d = line.Dir;
            Vec2d n = line.Normal;
            Vec2d a = line.a;
            var list = new List<int>(VertexCount / 2);
            for (int i = 0; i < VertexCount; i++)
            {
                double side = (_pos[i].x - a.x) * n.x + (_pos[i].y - a.y) * n.y;
                if (side * sideSign > FlapEpsilon) list.Add(i);
            }
            return list.ToArray();
        }

        public double MaxSignedDistance(FoldLine line, int sideSign)
        {
            Vec2d n = line.Normal;
            Vec2d a = line.a;
            double best = 0.0;
            for (int i = 0; i < VertexCount; i++)
            {
                double side = ((_pos[i].x - a.x) * n.x + (_pos[i].y - a.y) * n.y) * sideSign;
                if (side > best) best = side;
            }
            return best;
        }

        public FoldCommand Fold(FoldLine line, double angleDeg, int sideSign)
        {
            if (!line.IsValid || Math.Abs(angleDeg) < MinFoldAngle || sideSign == 0) return null;

            int[] idx = CollectFlapIndices(line, sideSign);
            if (idx.Length == 0) return null;

            double rad = angleDeg * Math.PI / 180.0;
            double cos = Math.Cos(rad);
            double sin = Math.Sin(rad);
            Vec2d d = line.Dir;
            Vec2d n = line.Normal;

            var cmd = new FoldCommand();
            cmd.line = line;
            cmd.angleDeg = angleDeg;
            cmd.sideSign = sideSign;
            cmd.indices = idx;
            cmd.prevPos = new Vec3d[idx.Length];
            cmd.prevLayer = new int[idx.Length];

            for (int k = 0; k < idx.Length; k++)
            {
                int i = idx[k];
                cmd.prevPos[k] = _pos[i];
                cmd.prevLayer[k] = _layer[i];
                _pos[i] = RotateAboutLine(_pos[i], line.a, d, n, cos, sin);
                int next = _layer[i] + 1;
                // Layer cap is gameplay (fold 6 becomes a decal); clamping keeps the
                // render stack finite instead of letting the paper climb off screen.
                _layer[i] = next > MaxLayer ? MaxLayer : next;
            }

            _undo.Add(cmd);
            _hasPreview = false;
            _previewIdx = null;
            return cmd;
        }

        // Restores only the vertices the command touched; a full 1089-snapshot per fold
        // would make undo cost scale with paper size instead of with the flap.
        public bool UndoLast()
        {
            if (_undo.Count == 0) return false;
            FoldCommand cmd = _undo[_undo.Count - 1];
            _undo.RemoveAt(_undo.Count - 1);
            for (int k = 0; k < cmd.indices.Length; k++)
            {
                int i = cmd.indices[k];
                _pos[i] = cmd.prevPos[k];
                _layer[i] = cmd.prevLayer[k];
            }
            _hasPreview = false;
            _previewIdx = null;
            return true;
        }

        public void BeginPreview(FoldLine line, double angleDeg, int sideSign)
        {
            if (!line.IsValid) return;
            _previewLine = line;
            _previewSide = sideSign;
            _previewIdx = CollectFlapIndices(line, sideSign);
            Array.Copy(_pos, _previewPos, VertexCount);
            Array.Copy(_layer, _previewLayer, VertexCount);
            for (int k = 0; k < _previewIdx.Length; k++)
            {
                int i = _previewIdx[k];
                int next = _layer[i] + 1;
                _previewLayer[i] = next > MaxLayer ? MaxLayer : next;
            }
            _hasPreview = true;
            UpdatePreview(angleDeg);
        }

        // Only the flap is recomputed each frame (the rest was copied once at BeginPreview),
        // so a drag costs a few hundred rotations instead of a full grid rebuild.
        public void UpdatePreview(double angleDeg)
        {
            if (!_hasPreview || _previewIdx == null) return;
            _previewAngleDeg = angleDeg;

            double rad = angleDeg * Math.PI / 180.0;
            double cos = Math.Cos(rad);
            double sin = Math.Sin(rad);
            Vec2d d = _previewLine.Dir;
            Vec2d n = _previewLine.Normal;

            for (int k = 0; k < _previewIdx.Length; k++)
            {
                int i = _previewIdx[k];
                _previewPos[i] = RotateAboutLine(_pos[i], _previewLine.a, d, n, cos, sin);
            }
        }

        public void ClearPreview()
        {
            _hasPreview = false;
            _previewIdx = null;
        }

        Vec3d[] Source(bool usePreview)
        {
            return usePreview && _hasPreview ? _previewPos : _pos;
        }

        public Bounds2D GetBounds(bool usePreview)
        {
            Vec3d[] src = Source(usePreview);
            double minX = double.MaxValue;
            double minY = double.MaxValue;
            double maxX = double.MinValue;
            double maxY = double.MinValue;
            for (int i = 0; i < VertexCount; i++)
            {
                if (src[i].x < minX) minX = src[i].x;
                if (src[i].y < minY) minY = src[i].y;
                if (src[i].x > maxX) maxX = src[i].x;
                if (src[i].y > maxY) maxY = src[i].y;
            }
            Bounds2D b = new Bounds2D();
            b.Min = new Vec2d(minX, minY);
            b.Max = new Vec2d(maxX, maxY);
            return b;
        }

        // Convex hull is the cheapest contour that is still exact enough to draw a debug
        // outline and to sanity-check the fold from outside the engine.
        public Vec2d[] GetHull(bool usePreview)
        {
            Vec3d[] src = Source(usePreview);
            var pts = new List<Vec2d>(VertexCount);
            for (int i = 0; i < VertexCount; i++) pts.Add(new Vec2d(src[i].x, src[i].y));
            pts.Sort(CompareXY);

            int n = pts.Count;
            if (n < 3) return pts.ToArray();

            var hull = new Vec2d[2 * n];
            int k = 0;
            for (int i = 0; i < n; i++)
            {
                while (k >= 2 && Vec2d.Cross(hull[k - 1] - hull[k - 2], pts[i] - hull[k - 2]) <= 1e-12) k--;
                hull[k++] = pts[i];
            }
            for (int i = n - 2, lower = k + 1; i >= 0; i--)
            {
                while (k >= lower && Vec2d.Cross(hull[k - 1] - hull[k - 2], pts[i] - hull[k - 2]) <= 1e-12) k--;
                hull[k++] = pts[i];
            }

            var result = new Vec2d[k - 1];
            Array.Copy(hull, result, k - 1);
            return result;
        }

        static int CompareXY(Vec2d a, Vec2d b)
        {
            if (a.x < b.x) return -1;
            if (a.x > b.x) return 1;
            if (a.y < b.y) return -1;
            if (a.y > b.y) return 1;
            return 0;
        }

        public void CopyProjected(double[] xs, double[] ys, bool usePreview)
        {
            Vec3d[] src = Source(usePreview);
            int n = VertexCount;
            if (xs.Length < n) n = xs.Length;
            if (ys.Length < n) n = ys.Length;
            for (int i = 0; i < n; i++)
            {
                xs[i] = src[i].x;
                ys[i] = src[i].y;
            }
        }

        public void BuildUnityMesh(Mesh mesh)
        {
            if (mesh == null) return;
            mesh.Clear();
            mesh.MarkDynamic();
            // Vertices must exist before indices or Unity rejects the triangle buffer.
            ApplyToUnityMesh(mesh, false);
            mesh.uv = _uv;
            mesh.triangles = _tri;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
        }

        public void ApplyToUnityMesh(Mesh mesh, bool usePreview)
        {
            if (mesh == null) return;
            Vec3d[] src = Source(usePreview);
            int[] lay = usePreview && _hasPreview ? _previewLayer : _layer;

            for (int i = 0; i < VertexCount; i++)
            {
                _renderVerts[i] = new Vector3(
                    (float)src[i].x,
                    (float)src[i].y,
                    (float)(src[i].z + lay[i] * LayerGap));

                // Vertex shade encodes layer so the 3-layer check is visible even when the
                // assigned material ignores normals; a material without vertex colour simply
                // drops it, which is harmless.
                int shade = 255 - lay[i] * 26;
                _renderColors[i] = new Color32((byte)shade, (byte)shade, (byte)shade, 255);
            }

            mesh.vertices = _renderVerts;
            mesh.colors32 = _renderColors;
        }

        // Replay compares this instead of raw doubles: quantising at 1e-6 keeps the hash
        // stable across machines whose libm differs in the last ulp.
        public ulong ComputeHash()
        {
            const double quantum = 1e-6;
            ulong h = 1469598103934665603UL;
            for (int i = 0; i < VertexCount; i++)
            {
                h = Mix(h, (long)Math.Round(_pos[i].x / quantum));
                h = Mix(h, (long)Math.Round(_pos[i].y / quantum));
                h = Mix(h, (long)Math.Round(_pos[i].z / quantum));
                h = Mix(h, _layer[i]);
            }
            return h;
        }

        static ulong Mix(ulong h, long value)
        {
            h ^= (ulong)value;
            h *= 1099511628211UL;
            return h;
        }
    }
}
