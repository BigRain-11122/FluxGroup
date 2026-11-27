using UnityEngine;

namespace FoldSpike
{
    // Procedural paper: fibre noise + faint horizontal grain + soft edge shading. No art assets,
    // because the spike has to prove the fold reads as paper, not that we can author a texture.
    public sealed class PaperLook : MonoBehaviour
    {
        public int Size = 256;
        public Color Base = new Color(0.965f, 0.955f, 0.925f);

        void Start() { Apply(); }

        public void Apply()
        {
            Texture2D tex = new Texture2D(Size, Size, TextureFormat.RGBA32, false);
            tex.name = "PaperProcedural";
            tex.wrapMode = TextureWrapMode.Clamp;
            tex.filterMode = FilterMode.Bilinear;

            Color32[] px = new Color32[Size * Size];
            System.Random rnd = new System.Random(7);
            for (int y = 0; y < Size; y++)
            {
                for (int x = 0; x < Size; x++)
                {
                    // Long fibres along x plus a light per-pixel grain.
                    float fibre = Mathf.Sin(x * 0.11f + Mathf.Sin(y * 0.037f) * 2.1f) * 0.006f;
                    float grain = ((float)rnd.NextDouble() - 0.5f) * 0.022f;
                    float row = Mathf.Sin(y * 0.9f) * 0.004f;

                    float nx = (x / (float)Size - 0.5f) * 2f;
                    float ny = (y / (float)Size - 0.5f) * 2f;
                    float edge = 1f - 0.05f * (nx * nx + ny * ny);

                    float k = 1f + fibre + grain + row;
                    Color c = Base * k * edge;
                    px[y * Size + x] = new Color32(
                        (byte)Mathf.Clamp(c.r * 255f, 0, 255),
                        (byte)Mathf.Clamp(c.g * 255f, 0, 255),
                        (byte)Mathf.Clamp(c.b * 255f, 0, 255), 255);
                }
            }
            tex.SetPixels32(px);
            tex.Apply();

            Renderer r = GetComponent<Renderer>();
            if (r != null && r.material != null) r.material.mainTexture = tex;
        }
    }
}
