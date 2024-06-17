using Basler.Pylon;
using System;
using System.Collections.Generic;

public class Camera : IDisposable {
    public Basler.Pylon.Camera camera;


    public Camera(int width, int height) {
        PrepareCamera(width, height);
    }

    public static void Display(CameraImage data, int f = 0) {
        var d = data.image;
        if (data.roiImage != null) {
            d = new byte[d.Length];
            Array.Copy(data.image, d, d.Length);
            DrawBox(d, data.roiX1, data.roiX2, data.roiY1, data.roiY2, data.width, data.height, 0xFF);
        }
        Display(d, data.width, data.height, f);
    }

    public static void Display(byte[] data, int width, int height, int f = 0) {
        ImageWindow.DisplayImage(f, data, PixelType.Mono8, width, height, 0, ImageOrientation.TopDown);
    }

    private static void DrawBox(byte[] data, int x1, int x2, int y1, int y2, int w, int h, byte boxColor) {
        for (int x = x1; x <= x2; x++) {
            data[y1 * w + x] = boxColor;
            data[y2 * w + x] = boxColor;
        }
        for (int y = y1; y <= y2; y++) {
            data[y * w + x1] = boxColor;
            data[y * w + x2] = boxColor;
        }
    }

    public class CameraImage {
        public byte[] image;
        public byte[] roiImage;
        public int width;
        public int height;
        public int roiWidth { get { return 1 + roiX2 - roiX1; } }
        public int roiHeight { get { return 1 + roiY2 - roiY1; } }
        public int roiX1;
        public int roiY1;
        public int roiX2;
        public int roiY2;
    }


    public CameraImage Acquire(float X = 0, float Y = 0, float W = 1, float H = 1) {
        var image = new CameraImage();
        camera.ExecuteSoftwareTrigger();
        camera.WaitForFrameTriggerReady(5000, TimeoutHandling.ThrowException);
        IGrabResult grabResult = camera.StreamGrabber.RetrieveResult(5000, TimeoutHandling.ThrowException);
        using (grabResult) {
            // Image grabbed successfully?
            if (grabResult.GrabSucceeded) {
                image.image = grabResult.PixelData as byte[];
                image.width = grabResult.Width;
                image.height = grabResult.Height;
                ComputeROI(ref image, X, Y, W, H);
            } else {
                Console.WriteLine("Grab Error: {0} {1}", grabResult.ErrorCode, grabResult.ErrorDescription);
            }
        }
        return image;
    }

    protected static void ComputeROI(ref CameraImage data, float X, float Y, float W, float H) {
        data.roiX1 = (int)((data.width - 1) * X);
        data.roiY1 = (int)((data.height - 1) * Y);
        int w = (int)(data.width * W);
        int h = (int)(data.height * H);
        data.roiX2 = Math.Min(data.width - 1, data.roiX1 + w);
        data.roiY2 = Math.Min(data.height - 1, data.roiY1 + h);

        w = 1+data.roiX2 - data.roiX1; 
        h = 1+data.roiY2 - data.roiY1;
        data.roiImage = new byte[w * h];
        for (int x = 0; x < w; x++) {
            for (int y = 0; y < h; y++) {
                int xd = x + data.roiX1;
                int yd = y + data.roiY1;
                data.roiImage[y * w + x] = data.image[yd * data.width + xd];
            }
        }
    }

    public void Dispose() {
        if (camera != null) {
            camera.Dispose();
        }
    }

    public void PrepareCamera(int width, int height) {
        if(camera != null) {
            return;
        }
        var info = CameraFinder.Enumerate();
        Console.WriteLine(info.Count);
        if(info.Count == 0) {
            Console.WriteLine("Could not find a camera.");
            return;
        }
        camera = new Basler.Pylon.Camera();
        // Set the acquisition mode to free running continuous acquisition when the camera is opened.
        camera.CameraOpened += Configuration.SoftwareTrigger;
        // Open the connection to the camera device.
        camera.Open();

        // The parameter MaxNumBuffer can be used to control the amount of buffers
        // allocated for grabbing. The default value of this parameter is 10.
        camera.Parameters[PLCameraInstance.MaxNumBuffer].SetValue(5);
        camera.Parameters[PLCamera.ExposureTime].SetToMinimum();
        camera.Parameters[PLCamera.Width].SetValue(width);
        camera.Parameters[PLCamera.Height].SetValue(height);

        // Start grabbing.
        camera.StreamGrabber.Start();

        // Print the model name of the camera.
        Console.WriteLine("Using camera {0}.", camera.CameraInfo[CameraInfoKey.ModelName]);
    }
}

public class DummyCamera : Camera {
    public int width, height;
    public DummyCamera(int width, int height) : base(width, height){
    }

    new public CameraImage Acquire(float X = 0, float Y = 0, float W = 1, float H = 1) {
        var image = new CameraImage();
        image.width = width;
        image.height = height;
        image.image = new byte[width * height];
        var r = new Random();
        r.NextBytes(image.image);
        ComputeROI(ref image, X, Y, W, H);
        return image;
    }
}