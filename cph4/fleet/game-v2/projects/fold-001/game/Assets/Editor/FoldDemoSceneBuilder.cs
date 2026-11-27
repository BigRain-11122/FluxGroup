using System;
using System.Collections.Generic;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace FoldSpike.Editor
{
    // Builds the playable demo scene and, on request, the Windows player that the automated
    // playtest and benchmark run against. Editor-only.
    public static class FoldDemoSceneBuilder
    {
        const string SceneDir = "Assets/Scenes";
        const string ScenePath = "Assets/Scenes/FoldDemo.unity";
        const string MaterialDir = "Assets/Materials";
        const string MaterialPath = "Assets/Materials/FoldPaper.mat";
        const string ResourceDir = "Assets/Resources";
        const string BuildDir = "Builds";
        const string ExeName = "FoldDemo.exe";

        [MenuItem("FoldSpike/Build Demo Scene")]
        public static void BuildDemoScene()
        {
            Debug.Log("[FoldDemo] scene -> " + ScenePath + "\n" + BuildScene());
        }

        [MenuItem("FoldSpike/Build Demo Player")]
        public static void BuildDemoPlayer()
        {
            Debug.Log("[FoldDemo] scene -> " + ScenePath + "\n" + BuildScene());
            string exe = ExportPlayer();
            Debug.Log("[FoldDemo] player -> " + exe);
        }

        // Batch entry: scene + player + a manifest, so a run can be reproduced from one command.
        public static void BuildAll()
        {
            string projectRoot = Path.GetDirectoryName(Application.dataPath);
            SyncResources(projectRoot);
            string sceneMsg = BuildScene();
            string exe = ExportPlayer();

            string manifest = Path.Combine(projectRoot, "Builds", "manifest.json");
            var sb = new System.Text.StringBuilder();
            sb.Append("{\n  \"scene\": \"").Append(ScenePath).Append("\",\n");
            sb.Append("  \"exe\": \"").Append(exe.Replace("\\", "/")).Append("\",\n");
            sb.Append("  \"size_bytes\": ").Append(new FileInfo(exe).Length).Append(",\n");
            sb.Append("  \"engine\": \"2022.3.62t17\",\n");
            sb.Append("  \"built_at\": \"").Append(DateTime.Now.ToString("yyyy-MM-ddTHH:mm:ss")).Append("\"\n}\n");
            File.WriteAllText(manifest, sb.ToString());
            Debug.Log("[FoldDemo] manifest -> " + manifest + "\n" + sceneMsg);
        }

        // data/garments.json is the source of truth; the build needs a copy under Resources.
        static void SyncResources(string projectRoot)
        {
            string src = Path.Combine(projectRoot, "..", "data", "garments.json");
            string dst = Path.Combine(projectRoot, "Assets", "Resources", "garments.json");
            if (!File.Exists(src))
            {
                Debug.LogWarning("[FoldDemo] source data missing: " + Path.GetFullPath(src));
                return;
            }
            Directory.CreateDirectory(Path.GetDirectoryName(dst));
            File.Copy(src, dst, true);
            AssetDatabase.Refresh();   // without this the copy is not imported before the build
            Debug.Log("[FoldDemo] synced garments.json -> " + dst);
        }

        static string BuildScene()
        {
            if (!AssetDatabase.IsValidFolder(SceneDir)) AssetDatabase.CreateFolder("Assets", "Scenes");
            if (!AssetDatabase.IsValidFolder(ResourceDir)) AssetDatabase.CreateFolder("Assets", "Resources");

            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            GameObject camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            Camera cam = camGo.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 0.5f;
            cam.nearClipPlane = 0.1f;
            cam.farClipPlane = 100f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.14f, 0.15f, 0.17f, 1f);
            camGo.transform.position = new Vector3(0f, 0f, -10f);

            GameObject paper = new GameObject("Paper");
            MeshFilter paperFilter = paper.AddComponent<MeshFilter>();
            MeshRenderer paperRenderer = paper.AddComponent<MeshRenderer>();
            Material mat = EnsureMaterial();
            if (mat != null) paperRenderer.sharedMaterial = mat;
            paper.AddComponent<PaperLook>();

            GameObject root = new GameObject("FoldDemo");
            FoldController controller = root.AddComponent<FoldController>();
            DrawerController drawer = root.AddComponent<DrawerController>();
            FoldGame game = root.AddComponent<FoldGame>();
            root.AddComponent<DemoLauncher>();

            GameObject drawerGo = new GameObject("Drawer");
            drawerGo.transform.SetParent(root.transform, false);
            Transform[] slots = new Transform[DrawerController.SlotCount];
            for (int i = 0; i < DrawerController.SlotCount; i++)
            {
                GameObject slot = new GameObject("Slot" + i);
                slot.transform.SetParent(drawerGo.transform, false);
                float x = (i - (DrawerController.SlotCount - 1) * 0.5f) * 0.18f;
                slot.transform.localPosition = new Vector3(x, -0.52f, 0f);
                slots[i] = slot.transform;
            }
            drawer.Slots = slots;
            drawer.SlotPitch = 0.18f;

            controller.Cam = cam;
            controller.PaperMeshFilter = paperFilter;
            controller.PaperWidth = 1.0f;
            controller.PaperHeight = 0.7f;
            controller.SnapScreenPercent = 0.03f;
            controller.MinCommitAngle = 25.0f;
            controller.SettleSeconds = 0.15f;
            controller.UseLegacyInput = false;  // FoldGame drives the pointer
            controller.TraceFolds = true;       // keep the fold probes in the demo build
            controller.Candidates = new List<CandidateFold>();

            game.Controller = controller;
            game.Drawer = drawer;
            game.Cam = cam;
            game.PaperRoot = paper.transform;
            game.RoomId = 1;
            game.ItemsPerDrawer = DrawerController.SlotCount;
            game.AutoLoad = true;

            EditorUtility.SetDirty(controller);
            EditorUtility.SetDirty(drawer);
            EditorUtility.SetDirty(game);
            EditorSceneManager.MarkSceneDirty(scene);

            if (!EditorSceneManager.SaveScene(scene, ScenePath))
            {
                throw new InvalidOperationException("scene save failed: " + ScenePath);
            }
            AssetDatabase.SaveAssets();

            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            return "saved; build settings updated";
        }

        static string ExportPlayer()
        {
            string projectRoot = Path.GetDirectoryName(Application.dataPath);
            string outDir = Path.Combine(projectRoot, BuildDir);
            Directory.CreateDirectory(outDir);
            string exe = Path.Combine(outDir, ExeName);

            PlayerSettings.productName = "FoldDemo";
            PlayerSettings.companyName = "FluxGame";
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.resizableWindow = false;
            PlayerSettings.runInBackground = true;

            BuildReport report = BuildPipeline.BuildPlayer(
                new[] { ScenePath }, exe, BuildTarget.StandaloneWindows64, BuildOptions.None);

            if (report.summary.result != BuildResult.Succeeded)
            {
                throw new InvalidOperationException("build failed: " + report.summary.result
                    + " errors=" + report.summary.totalErrors);
            }
            return exe;
        }

        static Material EnsureMaterial()
        {
            Material existing = AssetDatabase.LoadAssetAtPath<Material>(MaterialPath);
            if (existing != null) return existing;
            Shader shader = Shader.Find("Sprites/Default");
            if (shader == null) return null;
            if (!AssetDatabase.IsValidFolder(MaterialDir)) AssetDatabase.CreateFolder("Assets", "Materials");
            Material mat = new Material(shader);
            mat.name = "FoldPaper";
            AssetDatabase.CreateAsset(mat, MaterialPath);
            AssetDatabase.SaveAssets();
            return mat;
        }
    }
}
