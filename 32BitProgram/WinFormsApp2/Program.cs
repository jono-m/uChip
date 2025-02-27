using System.Diagnostics;
using System.IO;

namespace WinFormsApp2 {
    public static class Program {
        static Form1 plotterWindow;
        static Stopwatch timer = new Stopwatch();
        static Camera camera;
        static Camera.CameraImage lastImage;
        static int width = 512;
        static int height = 512;
        static int nFrames = 0;
        static Thread updateThread;
        static DataRecorder recorder;

        static StreamWriter w;

        static int c, m, y, k;

        public static void SetColor(int C, int M, int Y, int K) {
            c = C;
            m = M;
            y = Y;
            k = K;
            w.WriteLine(C.ToString() + "," + M.ToString() + "," + Y.ToString() + "," + K.ToString());
            w.Flush();
        }

        [STAThread]
        static void Main(string[] args) {
            recorder = new DataRecorder();

            var path = "C:/Users/jonoj/Repositories/uChip/uchipconduit.txt";
            w = File.CreateText(path);

            plotterWindow = new Form1();

            updateThread = new Thread(CameraLoop);
            updateThread.Start();

            System.Windows.Forms.Timer videoTimer = new System.Windows.Forms.Timer();
            videoTimer.Interval = 30;
            videoTimer.Tick += VideoUpdate;
            videoTimer.Start();

            System.Windows.Forms.Timer saveTimer = new System.Windows.Forms.Timer();
            saveTimer.Interval = 20000;
            saveTimer.Tick += DoSave;
            saveTimer.Start();


            SetColor(0, 0, 0, 0);

            Application.Run(plotterWindow);

            w.Dispose();
        }

        public static double TimeSinceStart {
            get {
                return timer.Elapsed.TotalMilliseconds / 1000;
            }
        }

        static Random r = new Random();

        static int[][] colors = new int[][]{ 
            new int[] { 255, 0, 0, 0 },
            new int[] { 0, 255, 0, 0 },
            new int[] { 0, 0, 255, 0},
            new int[] { 0, 0, 0, 255}};

        static int i = 0;
        static void DoSave(object sender, EventArgs args) {
            recorder.RecordImage(plotterWindow.GetBMP(), c, m, y, k);

            SetColor(colors[i][0], colors[i][1], colors[i][2], colors[i][3]);
            i++;
        }

        static void CameraLoop() {
            timer.Start();
            using (camera = new Camera(width, height)) {
                if (camera.camera == null) {
                    return;
                }
                while (!plotterWindow.IsDisposed) {
                    lastImage = camera.Acquire();
                    nFrames++;
                }
            }
        }

        static void VideoUpdate(object sender, EventArgs args) {
            if (lastImage != null) {
                plotterWindow.DisplayImage(lastImage);
            }
        }



    }
}