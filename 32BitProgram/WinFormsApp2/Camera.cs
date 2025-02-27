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
        public int width;
        public int height;
    }


    public CameraImage Acquire() {
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
            } else {
                Console.WriteLine("Grab Error: {0} {1}", grabResult.ErrorCode, grabResult.ErrorDescription);
            }
        }
        return image;
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
        camera.Parameters[PLCamera.PixelFormat].SetValue(PLCamera.PixelFormat.BGR8);
        camera.Parameters[PLCameraInstance.MaxNumBuffer].SetValue(5);
        camera.Parameters[PLCamera.ExposureTime].SetValue(2000);
        camera.Parameters[PLCamera.Width].SetValue(width);
        camera.Parameters[PLCamera.Height].SetValue(height);

        // Start grabbing.
        camera.StreamGrabber.Start();

        // Print the model name of the camera.
        Console.WriteLine("Using camera {0}.", camera.CameraInfo[CameraInfoKey.ModelName]);
    }
}