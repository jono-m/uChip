namespace WinFormsApp2 {
    partial class Form1 {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing) {
            if (disposing && (components != null)) {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent() {
            display = new PylonCamera.PictureBoxNN();
            ((System.ComponentModel.ISupportInitialize)display).BeginInit();
            SuspendLayout();
            // 
            // display
            // 
            display.Location = new Point(53, 12);
            display.Name = "display";
            display.Size = new Size(861, 880);
            display.TabIndex = 0;
            display.TabStop = false;
            // 
            // Form1
            // 
            AutoScaleDimensions = new SizeF(13F, 32F);
            AutoScaleMode = AutoScaleMode.Font;
            ClientSize = new Size(1172, 916);
            Controls.Add(display);
            Name = "Form1";
            Text = "Form1";
            ((System.ComponentModel.ISupportInitialize)display).EndInit();
            ResumeLayout(false);
        }

        #endregion

        private PylonCamera.PictureBoxNN display;
    }
}