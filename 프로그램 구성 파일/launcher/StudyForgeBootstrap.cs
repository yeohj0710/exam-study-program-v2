using System;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.Sockets;
using System.Security.Cryptography;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

internal static class Program
{
    [STAThread]
    private static void Main()
    {
        Application.EnableVisualStyles();
        Application.SetCompatibleTextRenderingDefault(false);
        Application.Run(new SplashForm());
    }
}

internal sealed class SplashForm : Form
{
    private readonly Label statusLabel;
    private readonly Label detailLabel;
    private readonly ProgressBar progressBar;
    private readonly Button cancelButton;
    private Process coreProcess;
    private bool closingAfterReady;

    public SplashForm()
    {
        Text = "StudyForge";
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.None;
        BackColor = Color.FromArgb(247, 247, 248);
        ClientSize = new Size(460, 230);
        ShowInTaskbar = true;
        Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point);

        Panel card = new Panel();
        card.BackColor = Color.White;
        card.Bounds = new Rectangle(18, 18, 424, 194);
        Controls.Add(card);

        LogoBox logo = new LogoBox();
        logo.Bounds = new Rectangle(28, 30, 54, 54);
        card.Controls.Add(logo);

        Label title = new Label();
        title.AutoSize = true;
        title.Text = "StudyForge";
        title.ForeColor = Color.FromArgb(32, 33, 35);
        title.Font = new Font("Segoe UI", 18F, FontStyle.Bold, GraphicsUnit.Point);
        title.Location = new Point(96, 29);
        card.Controls.Add(title);

        Label subtitle = new Label();
        subtitle.AutoSize = true;
        subtitle.Text = "\uc2dc\ud5d8 \uc790\ub8cc \uc554\uae30 \ud504\ub85c\uadf8\ub7a8";
        subtitle.ForeColor = Color.FromArgb(107, 111, 118);
        subtitle.Font = new Font("Malgun Gothic", 9.5F, FontStyle.Regular, GraphicsUnit.Point);
        subtitle.Location = new Point(98, 65);
        card.Controls.Add(subtitle);

        statusLabel = new Label();
        statusLabel.AutoSize = true;
        statusLabel.Text = "\uc900\ube44 \uc911";
        statusLabel.ForeColor = Color.FromArgb(32, 33, 35);
        statusLabel.Font = new Font("Malgun Gothic", 10F, FontStyle.Bold, GraphicsUnit.Point);
        statusLabel.Location = new Point(30, 106);
        card.Controls.Add(statusLabel);

        detailLabel = new Label();
        detailLabel.AutoSize = false;
        detailLabel.Text = "\uc11c\ubc84\uc640 \uc790\ub8cc\ub97c \ubd88\ub7ec\uc624\ub294 \uc911\uc785\ub2c8\ub2e4.";
        detailLabel.ForeColor = Color.FromArgb(107, 111, 118);
        detailLabel.Font = new Font("Malgun Gothic", 9F, FontStyle.Regular, GraphicsUnit.Point);
        detailLabel.Bounds = new Rectangle(30, 128, 360, 22);
        card.Controls.Add(detailLabel);

        progressBar = new ProgressBar();
        progressBar.Style = ProgressBarStyle.Marquee;
        progressBar.MarqueeAnimationSpeed = 18;
        progressBar.Bounds = new Rectangle(30, 158, 300, 8);
        card.Controls.Add(progressBar);

        cancelButton = new Button();
        cancelButton.Text = "\ucde8\uc18c";
        cancelButton.FlatStyle = FlatStyle.Flat;
        cancelButton.FlatAppearance.BorderColor = Color.FromArgb(222, 222, 227);
        cancelButton.BackColor = Color.White;
        cancelButton.ForeColor = Color.FromArgb(52, 53, 65);
        cancelButton.Bounds = new Rectangle(344, 146, 56, 30);
        cancelButton.Click += delegate { CancelLaunch(); };
        card.Controls.Add(cancelButton);

        Shown += async delegate { await StartAndMonitorAsync(); };
        FormClosing += OnFormClosing;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        using (SolidBrush brush = new SolidBrush(Color.FromArgb(35, 0, 0, 0)))
        {
            e.Graphics.FillRectangle(brush, 22, 22, 424, 194);
        }
    }

    private async Task StartAndMonitorAsync()
    {
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string appDir = Path.Combine(baseDir, "\ud504\ub85c\uadf8\ub7a8 \uad6c\uc131 \ud30c\uc77c");
        string coreExe = Path.Combine(appDir, "launcher", "StudyForgeCore.exe");

        if (!File.Exists(coreExe))
        {
            ShowError("\uc2e4\ud589 \ud30c\uc77c\uc744 \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.", coreExe);
            return;
        }

        string instanceId = InstanceId(appDir);
        DateTime startedAt = DateTime.UtcNow;

        try
        {
            ProcessStartInfo startInfo = new ProcessStartInfo(coreExe);
            startInfo.WorkingDirectory = baseDir;
            startInfo.UseShellExecute = false;
            startInfo.CreateNoWindow = true;
            startInfo.WindowStyle = ProcessWindowStyle.Hidden;
            startInfo.EnvironmentVariables["STUDYFORGE_NO_SPLASH"] = "1";
            coreProcess = Process.Start(startInfo);
        }
        catch (Exception ex)
        {
            ShowError("\uc2e4\ud589 \uc2dc\uc791\uc5d0 \uc2e4\ud328\ud588\uc2b5\ub2c8\ub2e4.", ex.Message);
            return;
        }

        while (!IsDisposed)
        {
            if (FindHealthyPort(instanceId) != null)
            {
                closingAfterReady = true;
                statusLabel.Text = "\ube0c\ub77c\uc6b0\uc800\ub97c \uc5ec\ub294 \uc911";
                detailLabel.Text = "\uc900\ube44\uac00 \ub05d\ub0ac\uc2b5\ub2c8\ub2e4.";
                await Task.Delay(650);
                Close();
                return;
            }

            if (coreProcess != null && coreProcess.HasExited)
            {
                int? existingPort = FindHealthyPort(instanceId);
                if (existingPort != null)
                {
                    closingAfterReady = true;
                    Close();
                    return;
                }

                ShowError("\uc2e4\ud589\uc774 \uc911\ub2e8\ub418\uc5c8\uc2b5\ub2c8\ub2e4.", "launcher-error.log\ub97c \ud655\uc778\ud574 \uc8fc\uc138\uc694.");
                return;
            }

            int elapsed = (int)(DateTime.UtcNow - startedAt).TotalSeconds;
            if (elapsed >= 12)
            {
                statusLabel.Text = "\uccab \uc2e4\ud589 \uc900\ube44 \uc911";
                detailLabel.Text = "\ucc98\uc74c \uc2e4\ud589\uc740 \uc790\ub8cc \ud655\uc778 \ub54c\ubb38\uc5d0 \uc870\uae08 \ub354 \uac78\ub9b4 \uc218 \uc788\uc2b5\ub2c8\ub2e4.";
            }

            await Task.Delay(350);
        }
    }

    private static string InstanceId(string appDir)
    {
        using (SHA1 sha1 = SHA1.Create())
        {
            byte[] hash = sha1.ComputeHash(Encoding.UTF8.GetBytes(appDir));
            StringBuilder builder = new StringBuilder();
            for (int index = 0; index < hash.Length; index++)
            {
                builder.Append(hash[index].ToString("x2"));
            }
            return builder.ToString().Substring(0, 16);
        }
    }

    private static int? FindHealthyPort(string instanceId)
    {
        for (int port = 8765; port <= 8785; port++)
        {
            try
            {
                if (!PortIsOpen(port))
                {
                    continue;
                }
                HttpWebRequest request = (HttpWebRequest)WebRequest.Create("http://127.0.0.1:" + port + "/api/health");
                request.Proxy = null;
                request.Timeout = 1200;
                request.ReadWriteTimeout = 1200;
                using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
                using (Stream stream = response.GetResponseStream())
                using (StreamReader reader = new StreamReader(stream, Encoding.UTF8))
                {
                    string body = reader.ReadToEnd();
                    if (body.IndexOf("\"instance_id\":\"" + instanceId + "\"", StringComparison.Ordinal) >= 0)
                    {
                        return port;
                    }
                    if (
                        body.IndexOf("\"ok\":true", StringComparison.Ordinal) >= 0 &&
                        body.IndexOf("\"instance_id\"", StringComparison.Ordinal) >= 0 &&
                        body.IndexOf("\"project_root\"", StringComparison.Ordinal) >= 0
                    )
                    {
                        return port;
                    }
                }
            }
            catch
            {
            }
        }
        return null;
    }

    private static bool PortIsOpen(int port)
    {
        TcpClient client = new TcpClient();
        try
        {
            IAsyncResult result = client.BeginConnect("127.0.0.1", port, null, null);
            if (!result.AsyncWaitHandle.WaitOne(80))
            {
                return false;
            }
            client.EndConnect(result);
            return true;
        }
        catch
        {
            return false;
        }
        finally
        {
            client.Close();
        }
    }

    private void ShowError(string title, string detail)
    {
        progressBar.Style = ProgressBarStyle.Continuous;
        progressBar.Value = 0;
        statusLabel.Text = title;
        detailLabel.Text = detail;
        cancelButton.Text = "\ub2eb\uae30";
    }

    private void CancelLaunch()
    {
        if (!closingAfterReady && coreProcess != null && !coreProcess.HasExited)
        {
            try
            {
                coreProcess.Kill();
            }
            catch
            {
            }
        }
        Close();
    }

    private void OnFormClosing(object sender, FormClosingEventArgs e)
    {
        if (!closingAfterReady && coreProcess != null && !coreProcess.HasExited)
        {
            try
            {
                coreProcess.Kill();
            }
            catch
            {
            }
        }
    }
}

internal sealed class LogoBox : Control
{
    public LogoBox()
    {
        DoubleBuffered = true;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        e.Graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;

        using (SolidBrush white = new SolidBrush(Color.White))
        using (SolidBrush teal = new SolidBrush(Color.FromArgb(15, 118, 110)))
        using (Font markFont = new Font("Segoe UI", 24F, FontStyle.Bold, GraphicsUnit.Pixel))
        using (StringFormat format = new StringFormat())
        {
            using (System.Drawing.Drawing2D.GraphicsPath path = new System.Drawing.Drawing2D.GraphicsPath())
            {
                const int radius = 10;
                Rectangle rect = new Rectangle(0, 0, 54, 54);
                path.AddArc(rect.Left, rect.Top, radius * 2, radius * 2, 180, 90);
                path.AddArc(rect.Right - radius * 2 - 1, rect.Top, radius * 2, radius * 2, 270, 90);
                path.AddArc(rect.Right - radius * 2 - 1, rect.Bottom - radius * 2 - 1, radius * 2, radius * 2, 0, 90);
                path.AddArc(rect.Left, rect.Bottom - radius * 2 - 1, radius * 2, radius * 2, 90, 90);
                path.CloseFigure();
                e.Graphics.FillPath(teal, path);
            }

            format.Alignment = StringAlignment.Center;
            format.LineAlignment = StringAlignment.Center;
            e.Graphics.DrawString("SF", markFont, white, new RectangleF(2, 2, 50, 50), format);
        }
    }
}
