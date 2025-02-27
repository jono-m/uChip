using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace PylonCamera {
    class PictureBoxNN : PictureBox {
        public Rectangle r;
        protected override void OnPaint(PaintEventArgs pe) {
            if(Image == null) {
                return;
            }
            pe.Graphics.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.NearestNeighbor;
            pe.Graphics.DrawImage(Image, pe.ClipRectangle);
            var pen = new Pen(Color.Red);
            r.Width -= 1;
            r.Height -= 1;
            pe.Graphics.DrawRectangle(pen, r);
        }
    }
}
