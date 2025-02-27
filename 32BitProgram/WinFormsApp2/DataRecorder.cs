using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Xml.Linq;
using static Camera;

namespace WinFormsApp2 {
    public class DataRecorder {
        private StreamWriter file;

        string folderPath;

        public struct C {
            public int c, m, y, k;
            public C(int c, int m, int y, int k) {
                this.c = c;
                this.m = m;
                this.y = y;
                this.k = k;
            }
        }

        public Dictionary<C, int> colorCount;

        public DataRecorder() {
            colorCount = new Dictionary<C, int>();
            folderPath = "Data_" + DateTime.Now.ToString("yyyy-MM-dd-HH-mm-ss");
            var p = Directory.CreateDirectory(folderPath);
            folderPath = p.FullName;
        }

        public void RecordImage(Bitmap image, int c, int m, int y, int k) {
            var col = new C(c, m, y, k);
            if(!colorCount.ContainsKey(col)) {
                colorCount[col] = 0;
            }
            int n = colorCount[col];
            colorCount[col] += 1;
            string p = folderPath + "/image_" + c + "_" + m + "_" + y + "_" + k + "_" + n + ".png";
            Console.WriteLine("Saved to '" + p + "'");
            image.Save(p);
        }
    }
}
