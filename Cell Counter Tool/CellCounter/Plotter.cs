using ScottPlot.Plottables;
using ScottPlot.WinForms;
using System.Collections.Generic;
using System;
using System.Drawing;
using System.Linq;
using System.Windows.Forms;
using System.Diagnostics;

public partial class Plotter : Form {

    FormsPlot motionPlot;
    FormsPlot cellCountPlot;
    Bitmap bitmap;

    readonly List<ScottPlot.Coordinates> motionPointsA = new List<ScottPlot.Coordinates>();
    readonly List<ScottPlot.Coordinates> motionPointsB = new List<ScottPlot.Coordinates>();
    readonly List<ScottPlot.Coordinates> detectedPointsA = new List<ScottPlot.Coordinates>();
    readonly List<ScottPlot.Coordinates> detectedPointsB = new List<ScottPlot.Coordinates>();
    bool isACurrent;

    readonly List<float> cellsPerSecond = new List<float>();
    readonly List<float> cellsPerSecondLogTimes = new List<float>();
    readonly VerticalLine timeMarkerLine;
    readonly HorizontalLine thresholdLine;
    double motionDisplayWidth;
    double motionLeftTime;
    double motionRightTime;
    public Plotter(double motionDisplayWidth) {
        this.motionDisplayWidth = motionDisplayWidth; 
        InitializeComponent();
        motionPlot = new FormsPlot() { Dock = DockStyle.Fill };
        cellCountPlot = new FormsPlot { Dock = DockStyle.Fill };
        motionPlotPanel.Controls.Add(motionPlot);
        cellCountPlotPanel.Controls.Add(cellCountPlot);

        timeMarkerLine = motionPlot.Plot.Add.VerticalLine(0, 2, color: new ScottPlot.Color(100, 0, 0));
        thresholdLine = motionPlot.Plot.Add.HorizontalLine(0, 2, color: new ScottPlot.Color(0, 100, 100));

        cellCountPlot.Plot.Add.ScatterLine(cellsPerSecondLogTimes, cellsPerSecond);
        cellCountPlot.Plot.XLabel("Time (s)");
        cellCountPlot.Plot.YLabel("Cells/second");

        motionPlot.Plot.Add.ScatterLine(motionPointsA, color: new ScottPlot.Color(0, 0, 0));
        motionPlot.Plot.Add.ScatterPoints(detectedPointsA, color: new ScottPlot.Color(0, 255, 0));

        motionPlot.Plot.Add.ScatterLine(motionPointsB, color: new ScottPlot.Color(0, 0, 0));
        motionPlot.Plot.Add.ScatterPoints(detectedPointsB, color: new ScottPlot.Color(0, 255, 0));
        motionPlot.Plot.XLabel("Time (s)");
        motionPlot.Plot.YLabel("Motion");
        motionPlot.Plot.Axes.SetLimitsX(0, motionDisplayWidth);
    }

    public void UpdateLabels(double fps, int nDetected) {
        this.fpsLabel.Text = "FPS: " + fps.ToString();
        totalDetectedLabel.Text = "Detected " + nDetected;
        x = roiXBar.Value / 100.0f;
        y = roiYBar.Value / 100.0f;
        w = roiWBar.Value / 100.0f;
        h = roiHBar.Value / 100.0f;
    }

    public void AddCellsPerSecond(float cps) {
        cellsPerSecond.Add(cps);
        cellsPerSecondLogTimes.Add((float)Program.TimeSinceStart);
    } 

    public float GetThreshold() {
        return (float)cutoff.Value;
    }

    public void DisplayImage(Camera.CameraImage image) {
        if(bitmap == null || bitmap.Width != image.width || bitmap.Height != bitmap.Height) {
            if(bitmap != null) {
                bitmap.Dispose();
            }
            bitmap = new Bitmap(image.width, image.height);
            display.Image = bitmap;
        }
        for (int x = 0; x < image.width; x++) {
            for(int y = 0; y < image.height; y++) {
                int I = image.image[y * image.width + x];
                var color = Color.FromArgb(I, I, I);
                //if(((x == image.roiX1 || x == image.roiX2) && y >= image.roiY1 && y <= image.roiY2) ||
                //   ((y == image.roiY1 || y == image.roiY2) && x >= image.roiX1 && x <= image.roiX2)) {
                //    color = Color.Red;
                //}
                bitmap.SetPixel(x, y, color);
            }
        }
        display.r = new System.Drawing.Rectangle((int)(((float)image.roiX1) / image.width * display.Width),
                                                 (int)(((float)image.roiY1) / image.height* display.Height),
                                                 (int)(((float)image.roiWidth) / image.width * display.Width),
                                                 (int)(((float)image.roiHeight) / image.height* display.Height));
        display.Refresh();
    }

    private float x, y, w, h;
    public void GetRect(out float x, out float y, out float w, out float h) {
        x = this.x;
        y = this.y;
        w = this.w;
        h = this.h;
    }

    public void AddMotionDataPoint(CellDetector.MotionData motionData) {
        lock(motionPointsA) { 
            double t = motionData.time - motionLeftTime;
            var motionPoints = isACurrent ? motionPointsA : motionPointsB;
            var detectedPoints = isACurrent ? detectedPointsA : detectedPointsB;
            motionPoints.Add(new ScottPlot.Coordinates(t, motionData.motionAmount));
            if (motionData.cellWasDetected) {
                detectedPoints.Add(new ScottPlot.Coordinates(t, -5));
            }
        }
    }

    public void RefreshPlots() {
        var t = Program.TimeSinceStart;
        if (t > motionRightTime) {
            motionLeftTime = motionRightTime;
            motionRightTime = motionLeftTime + motionDisplayWidth;
            isACurrent = !isACurrent;
            var motionPoints = isACurrent ? motionPointsA : motionPointsB;
            var detectedPoints = isACurrent ? detectedPointsA : detectedPointsB;
            motionPoints.Clear();
            detectedPoints.Clear();
        }
        t = t - motionLeftTime;

        thresholdLine.Position = GetThreshold();
        timeMarkerLine.Position = t;

        // Now need to purge the old one
        var oldMotionPoints = isACurrent ? motionPointsB : motionPointsA;
        var oldDetectedPoints = isACurrent ? detectedPointsB : detectedPointsA;

        double cutoff = t + motionDisplayWidth * 0.05;
        for (int i = oldMotionPoints.Count - 1; i >= 0; i--) {
            if (oldMotionPoints[i].X <= cutoff) {
                oldMotionPoints.RemoveAt(i);
            }
        }
        for (int i = oldDetectedPoints.Count - 1; i >= 0; i--) {
            if (oldDetectedPoints[i].X <= cutoff) {
                oldDetectedPoints.RemoveAt(i);
            }
        }

        double maxMotion = 0;
        lock(motionPointsA) { 
            var pts = motionPointsA.Concat(motionPointsB).Select(x => x.Y).DefaultIfEmpty();
            maxMotion = Math.Max(pts.Max(), thresholdLine.Position);
            motionPlot.Plot.Axes.SetLimitsY(-10, maxMotion * 1.1);
            motionPlot.Refresh();
        }

        float timeMax = cellsPerSecondLogTimes.Count == 0 ? 0 : cellsPerSecondLogTimes.Max();
        float cpsMax = cellsPerSecond.Count == 0 ? 0 : cellsPerSecond.Max();
        cellCountPlot.Plot.Axes.SetLimits(0, timeMax * 1.1f, 0, cpsMax * 1.1f);
        cellCountPlot.Refresh();
    }

    private void InitializeComponent() {
            this.panel2 = new System.Windows.Forms.Panel();
            this.label6 = new System.Windows.Forms.Label();
            this.label4 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.label2 = new System.Windows.Forms.Label();
            this.roiHBar = new System.Windows.Forms.TrackBar();
            this.roiWBar = new System.Windows.Forms.TrackBar();
            this.roiYBar = new System.Windows.Forms.TrackBar();
            this.roiXBar = new System.Windows.Forms.TrackBar();
            this.fpsLabel = new System.Windows.Forms.Label();
            this.label1 = new System.Windows.Forms.Label();
            this.cutoff = new System.Windows.Forms.NumericUpDown();
            this.motionPlotPanel = new System.Windows.Forms.Panel();
            this.cellCountPlotPanel = new System.Windows.Forms.Panel();
            this.totalDetectedLabel = new System.Windows.Forms.Label();
            this.display = new PylonCamera.PictureBoxNN();
            this.panel2.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.roiHBar)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.roiWBar)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.roiYBar)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.roiXBar)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.cutoff)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.display)).BeginInit();
            this.SuspendLayout();
            // 
            // panel2
            // 
            this.panel2.Controls.Add(this.label6);
            this.panel2.Controls.Add(this.label4);
            this.panel2.Controls.Add(this.label3);
            this.panel2.Controls.Add(this.label2);
            this.panel2.Controls.Add(this.roiHBar);
            this.panel2.Controls.Add(this.roiWBar);
            this.panel2.Controls.Add(this.roiYBar);
            this.panel2.Controls.Add(this.roiXBar);
            this.panel2.Location = new System.Drawing.Point(12, 626);
            this.panel2.Name = "panel2";
            this.panel2.Size = new System.Drawing.Size(517, 314);
            this.panel2.TabIndex = 1;
            // 
            // label6
            // 
            this.label6.AutoSize = true;
            this.label6.Location = new System.Drawing.Point(21, 91);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(69, 25);
            this.label6.TabIndex = 10;
            this.label6.Text = "ROI Y";
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(21, 201);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(69, 25);
            this.label4.TabIndex = 8;
            this.label4.Text = "ROI H";
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(21, 136);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(74, 25);
            this.label3.TabIndex = 7;
            this.label3.Text = "ROI W";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(21, 35);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(68, 25);
            this.label2.TabIndex = 6;
            this.label2.Text = "ROI X";
            // 
            // roiHBar
            // 
            this.roiHBar.Location = new System.Drawing.Point(97, 201);
            this.roiHBar.Maximum = 100;
            this.roiHBar.Name = "roiHBar";
            this.roiHBar.Size = new System.Drawing.Size(364, 90);
            this.roiHBar.TabIndex = 4;
            this.roiHBar.Value = 100;
            // 
            // roiWBar
            // 
            this.roiWBar.Location = new System.Drawing.Point(97, 136);
            this.roiWBar.Maximum = 100;
            this.roiWBar.Name = "roiWBar";
            this.roiWBar.Size = new System.Drawing.Size(364, 90);
            this.roiWBar.TabIndex = 3;
            this.roiWBar.Value = 100;
            // 
            // roiYBar
            // 
            this.roiYBar.Location = new System.Drawing.Point(97, 82);
            this.roiYBar.Maximum = 100;
            this.roiYBar.Name = "roiYBar";
            this.roiYBar.Size = new System.Drawing.Size(364, 90);
            this.roiYBar.TabIndex = 2;
            // 
            // roiXBar
            // 
            this.roiXBar.Location = new System.Drawing.Point(97, 26);
            this.roiXBar.Maximum = 100;
            this.roiXBar.Name = "roiXBar";
            this.roiXBar.Size = new System.Drawing.Size(364, 90);
            this.roiXBar.TabIndex = 1;
            // 
            // fpsLabel
            // 
            this.fpsLabel.AutoSize = true;
            this.fpsLabel.Location = new System.Drawing.Point(12, 580);
            this.fpsLabel.Name = "fpsLabel";
            this.fpsLabel.Size = new System.Drawing.Size(65, 25);
            this.fpsLabel.TabIndex = 13;
            this.fpsLabel.Text = "FPS: ";
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(546, 383);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(140, 25);
            this.label1.TabIndex = 11;
            this.label1.Text = "Motion Cutoff";
            // 
            // cutoff
            // 
            this.cutoff.DecimalPlaces = 3;
            this.cutoff.Location = new System.Drawing.Point(692, 381);
            this.cutoff.Maximum = new decimal(new int[] {
            10000000,
            0,
            0,
            0});
            this.cutoff.Name = "cutoff";
            this.cutoff.Size = new System.Drawing.Size(120, 31);
            this.cutoff.TabIndex = 14;
            // 
            // motionPlotPanel
            // 
            this.motionPlotPanel.Location = new System.Drawing.Point(551, 26);
            this.motionPlotPanel.Name = "motionPlotPanel";
            this.motionPlotPanel.Size = new System.Drawing.Size(572, 341);
            this.motionPlotPanel.TabIndex = 2;
            // 
            // cellCountPlotPanel
            // 
            this.cellCountPlotPanel.Location = new System.Drawing.Point(551, 435);
            this.cellCountPlotPanel.Name = "cellCountPlotPanel";
            this.cellCountPlotPanel.Size = new System.Drawing.Size(572, 438);
            this.cellCountPlotPanel.TabIndex = 3;
            // 
            // totalDetectedLabel
            // 
            this.totalDetectedLabel.AutoSize = true;
            this.totalDetectedLabel.Location = new System.Drawing.Point(546, 892);
            this.totalDetectedLabel.Name = "totalDetectedLabel";
            this.totalDetectedLabel.Size = new System.Drawing.Size(206, 25);
            this.totalDetectedLabel.TabIndex = 15;
            this.totalDetectedLabel.Text = "Total Cells Detected";
            // 
            // display
            // 
            this.display.Location = new System.Drawing.Point(17, 27);
            this.display.Name = "display";
            this.display.Size = new System.Drawing.Size(512, 512);
            this.display.SizeMode = System.Windows.Forms.PictureBoxSizeMode.CenterImage;
            this.display.TabIndex = 16;
            this.display.TabStop = false;
            // 
            // Plotter
            // 
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.None;
            this.ClientSize = new System.Drawing.Size(1159, 1018);
            this.Controls.Add(this.display);
            this.Controls.Add(this.totalDetectedLabel);
            this.Controls.Add(this.cutoff);
            this.Controls.Add(this.cellCountPlotPanel);
            this.Controls.Add(this.label1);
            this.Controls.Add(this.motionPlotPanel);
            this.Controls.Add(this.fpsLabel);
            this.Controls.Add(this.panel2);
            this.Name = "Plotter";
            this.FormClosed += new System.Windows.Forms.FormClosedEventHandler(this.Plotter_FormClosed);
            this.panel2.ResumeLayout(false);
            this.panel2.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.roiHBar)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.roiWBar)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.roiYBar)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.roiXBar)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.cutoff)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.display)).EndInit();
            this.ResumeLayout(false);
            this.PerformLayout();

    }

    private void Plotter_FormClosed(object sender, FormClosedEventArgs e) {
        if(bitmap != null) {
            bitmap.Dispose();
        }
    }
}