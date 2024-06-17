using System;
using System.Diagnostics;
using System.Threading;
using System.Windows.Forms;
public static class Program {
    static Plotter plotterWindow;
    static Stopwatch timer = new Stopwatch();
    static Camera camera;
    static double last;
    static Camera.CameraImage lastImage;
    static CellDetector detector;
    const double CountWidth = 10.0f;
    static int width = 128;
    static int height = 128;
    static bool save = true;
    static int nFrames = 0;
    static Thread updateThread;
    [STAThread]
    static void Main(string[] args) {
        //if(args.Length == 3) {
        //    int.TryParse(args[0], out var w);
        //    int.TryParse(args[1], out var h);
        //    int.TryParse(args[2], out var save);
        //    width = w;
        //    height = h;
        //    Program.save = save > 0;
        //}
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        plotterWindow = new Plotter(CountWidth);

        updateThread = new Thread(CameraLoop);
        updateThread.Start();

        System.Windows.Forms.Timer videoTimer = new System.Windows.Forms.Timer();
        videoTimer.Interval = 30;
        videoTimer.Tick += VideoUpdate;
        videoTimer.Start();

        System.Windows.Forms.Timer uiTimer = new System.Windows.Forms.Timer();
        uiTimer.Interval = 50;
        uiTimer.Tick += UIUpdate;
        uiTimer.Start();

        System.Windows.Forms.Timer cpsTimer = new System.Windows.Forms.Timer();
        cpsTimer.Interval = (int)CountWidth * 1000;
        cpsTimer.Tick += ComputeCPS;
        cpsTimer.Start();

        Application.Run(plotterWindow);
    }

    public static double TimeSinceStart {
        get {
            return timer.Elapsed.TotalMilliseconds / 1000;
        }
    }
    static void CameraLoop() {
        timer.Start();
        using (camera = new Camera(width, height)) {
            if(camera.camera == null) {
                return;
            }
            using (detector = new CellDetector(save)) {
                while (!plotterWindow.IsDisposed) {
                    Process();
                    nFrames++;
                }
            }
        }
    }

    static void Process() {
        plotterWindow.GetRect(out float roiX, out float roiY, out float roiW, out float roiH);
        lastImage = camera.Acquire(roiX, roiY, roiW, roiH);
        var motion = detector.ProcessImage(lastImage, plotterWindow.GetThreshold());
        plotterWindow.AddMotionDataPoint(motion);
    }

    static void VideoUpdate(object sender, EventArgs args) {
        if (lastImage != null) {
            plotterWindow.DisplayImage(lastImage);
        }
    }

    static void UIUpdate(object sender, EventArgs args) {
        if(!updateThread.IsAlive) {
            plotterWindow.Close();
            return;
        }
        if(detector == null) {
            return;
        }
        var c = TimeSinceStart;
        var fps = nFrames / (c - last);
        nFrames = 0;
        last = c;
        int count = detector.detectedCells.Count;
        plotterWindow.UpdateLabels(fps, count);
        plotterWindow.RefreshPlots();
    }
    static void ComputeCPS(object sender, EventArgs args) {
        float cps = detector.CalculateCellsPerSecond();
        plotterWindow.AddCellsPerSecond(cps);
    }
}