using System;
using UnityEngine;

namespace FoldSpike
{
    // Runtime entry point for the built demo. Keeps automation out of the shipped build path:
    // without these flags the exe is just the game.
    //
    //   FoldDemo.exe -autoplay -quit          one drawer, then exit (timings in the log)
    //   FoldDemo.exe -bench -benchfold -benchOut bench.json
    public sealed class DemoLauncher : MonoBehaviour
    {
        void Awake()
        {
            string[] args = Environment.GetCommandLineArgs();
            bool autoplay = Has(args, "-autoplay");
            bool bench = Has(args, "-bench");

            FoldGame game = GetComponent<FoldGame>();
            if (game == null) game = FindObjectOfType<FoldGame>();

            if (bench && game != null && Has(args, "-benchfold"))
            {
                game.PreFoldForBench();
            }

            if (autoplay && game != null)
            {
                AutoPlay ap = game.gameObject.AddComponent<AutoPlay>();
                ap.Game = game;
                ap.QuitWhenDone = Has(args, "-quit");
                ap.Active = true;
            }

            if (bench && game != null)
            {
                BenchmarkMode bm = game.gameObject.AddComponent<BenchmarkMode>();
                bm.Game = game;
                bm.OutPath = Value(args, "-benchOut") ?? "bench.json";
                bm.Frames = int.TryParse(Value(args, "-benchFrames"), out int n) ? n : 600;
            }
        }

        static bool Has(string[] args, string key)
        {
            for (int i = 0; i < args.Length; i++)
            {
                if (string.Equals(args[i], key, StringComparison.OrdinalIgnoreCase)) return true;
            }
            return false;
        }

        static string Value(string[] args, string key)
        {
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (string.Equals(args[i], key, StringComparison.OrdinalIgnoreCase)) return args[i + 1];
            }
            return null;
        }
    }
}
