using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace WinFormsApp2 {
    public partial class Form1 : Form {
        public Form1() {
            InitializeComponent();
            FormClosed += Plotter_FormClosed;
        }

        Bitmap bitmap;

        public Bitmap GetBMP() {
            return bitmap;
        }


        public void DisplayImage(Camera.CameraImage image) {
            if (bitmap == null || bitmap.Width != image.width || bitmap.Height != bitmap.Height) {
                if (bitmap != null) {
                    bitmap.Dispose();
                }
                bitmap = new Bitmap(image.width, image.height, System.Drawing.Imaging.PixelFormat.Format24bppRgb);
                display.Image = bitmap;
            }

            Rectangle rect = new Rectangle(0, 0, bitmap.Width, bitmap.Height);
            var data = bitmap.LockBits(rect, System.Drawing.Imaging.ImageLockMode.WriteOnly, System.Drawing.Imaging.PixelFormat.Format24bppRgb);

            IntPtr ptr = data.Scan0;

            int bytes = Math.Abs(data.Stride) * bitmap.Height;

            // Copy the RGB values back to the bitmap
            System.Runtime.InteropServices.Marshal.Copy(image.image, 0, ptr, bytes);

            bitmap.UnlockBits(data);

            display.Refresh();
        }

        private float x, y, w, h;
        public void GetRect(out float x, out float y, out float w, out float h) {
            x = this.x;
            y = this.y;
            w = this.w;
            h = this.h;
        }

        private void Plotter_FormClosed(object sender, FormClosedEventArgs e) {
            if (bitmap != null) {
                bitmap.Dispose();
            }
        }
    }
}
