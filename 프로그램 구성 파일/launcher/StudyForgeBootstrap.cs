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
    private readonly LoadingLine loadingLine;
    private readonly Button cancelButton;
    private Process coreProcess;
    private bool closingAfterReady;
    private bool launchStarted;

    public SplashForm()
    {
        Text = "Exam Study Program";
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.None;
        BackColor = Color.FromArgb(16, 17, 17);
        ClientSize = new Size(430, 132);
        ShowInTaskbar = true;
        Font = new Font("Segoe UI", 9F, FontStyle.Regular, GraphicsUnit.Point);
        Icon appIcon = LoadAppIcon();
        if (appIcon != null)
        {
            Icon = appIcon;
        }

        LogoBox logo = new LogoBox();
        logo.Bounds = new Rectangle(24, 32, 46, 46);
        Controls.Add(logo);

        Label title = new Label();
        title.AutoSize = true;
        title.Text = "Exam Study Program";
        title.ForeColor = Color.FromArgb(239, 238, 232);
        title.Font = new Font("Segoe UI", 13F, FontStyle.Bold, GraphicsUnit.Point);
        title.Location = new Point(92, 25);
        Controls.Add(title);

        Label subtitle = new Label();
        subtitle.AutoSize = true;
        subtitle.Text = "\ub85c\uceec \uc2dc\ud5d8 \uc554\uae30 \ub3c4\uad6c";
        subtitle.ForeColor = Color.FromArgb(150, 154, 151);
        subtitle.Font = new Font("Malgun Gothic", 8.5F, FontStyle.Regular, GraphicsUnit.Point);
        subtitle.Location = new Point(94, 52);
        Controls.Add(subtitle);

        statusLabel = new Label();
        statusLabel.AutoSize = false;
        statusLabel.AutoEllipsis = true;
        statusLabel.Text = "\uc900\ube44 \uc911";
        statusLabel.ForeColor = Color.FromArgb(239, 238, 232);
        statusLabel.Font = new Font("Malgun Gothic", 9F, FontStyle.Bold, GraphicsUnit.Point);
        statusLabel.Bounds = new Rectangle(94, 76, 238, 20);
        Controls.Add(statusLabel);

        detailLabel = new Label();
        detailLabel.AutoSize = false;
        detailLabel.AutoEllipsis = true;
        detailLabel.Text = "\uc790\ub8cc\ub97c \ud655\uc778\ud558\uace0 \uc788\uc2b5\ub2c8\ub2e4.";
        detailLabel.ForeColor = Color.FromArgb(150, 154, 151);
        detailLabel.Font = new Font("Malgun Gothic", 8.5F, FontStyle.Regular, GraphicsUnit.Point);
        detailLabel.Bounds = new Rectangle(94, 96, 238, 20);
        Controls.Add(detailLabel);

        loadingLine = new LoadingLine();
        loadingLine.Bounds = new Rectangle(94, 117, 238, 2);
        Controls.Add(loadingLine);

        cancelButton = new Button();
        cancelButton.Text = "\ucde8\uc18c";
        cancelButton.FlatStyle = FlatStyle.Flat;
        cancelButton.FlatAppearance.BorderColor = Color.FromArgb(54, 58, 57);
        cancelButton.BackColor = Color.FromArgb(24, 26, 26);
        cancelButton.ForeColor = Color.FromArgb(215, 213, 205);
        cancelButton.Bounds = new Rectangle(356, 52, 50, 30);
        cancelButton.Click += delegate { CancelLaunch(); };
        Controls.Add(cancelButton);

        Shown += async delegate { await StartAndMonitorAsync(); };
        FormClosing += OnFormClosing;
    }

    private static Icon LoadAppIcon()
    {
        string appDir = ResolveAppDir();
        string[] candidates = new string[]
        {
            Path.Combine(appDir, "public", "exam-study.ico"),
            Path.Combine(appDir, "dist", "exam-study.ico")
        };

        foreach (string candidate in candidates)
        {
            try
            {
                if (File.Exists(candidate))
                {
                    return new Icon(candidate);
                }
            }
            catch
            {
            }
        }

        return null;
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        using (Pen border = new Pen(Color.FromArgb(49, 55, 54)))
        {
            e.Graphics.DrawRectangle(border, 0, 0, ClientSize.Width - 1, ClientSize.Height - 1);
        }
    }

    private static string ResolveAppDir()
    {
        string folderName = "\ud504\ub85c\uadf8\ub7a8 \uad6c\uc131 \ud30c\uc77c";
        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string currentDir = Directory.GetCurrentDirectory();
        string[] candidates = new string[]
        {
            Path.Combine(baseDir, folderName),
            Path.Combine(currentDir, folderName)
        };

        foreach (string candidate in candidates)
        {
            try
            {
                if (Directory.Exists(candidate))
                {
                    return Path.GetFullPath(candidate);
                }
            }
            catch
            {
            }
        }

        return Path.Combine(baseDir, folderName);
    }

    private async Task StartAndMonitorAsync()
    {
        if (launchStarted)
        {
            return;
        }
        launchStarted = true;

        string baseDir = AppDomain.CurrentDomain.BaseDirectory;
        string appDir = ResolveAppDir();
        string coreExe = Path.Combine(appDir, "launcher", "ExamStudyCore.exe");

        if (!File.Exists(coreExe))
        {
            statusLabel.Text = "\uc2e4\ud589 \ud30c\uc77c\uc744 \uc900\ube44\ud558\uace0 \uc788\uc2b5\ub2c8\ub2e4.";
            detailLabel.Text = coreExe;
            if (!await WaitForFileAsync(coreExe, 20000))
            {
                ShowError("\uc2e4\ud589 \ud30c\uc77c\uc744 \ucc3e\uc744 \uc218 \uc5c6\uc2b5\ub2c8\ub2e4.", coreExe);
                return;
            }
        }

        string instanceId = InstanceId(appDir);
        DateTime startedAt = DateTime.UtcNow;
        int? alreadyRunningPort = FindHealthyPort(instanceId);
        if (alreadyRunningPort != null)
        {
            OpenUrl(alreadyRunningPort.Value);
            closingAfterReady = true;
            Close();
            return;
        }

        try
        {
            ProcessStartInfo startInfo = new ProcessStartInfo(coreExe);
            startInfo.WorkingDirectory = baseDir;
            startInfo.UseShellExecute = false;
            startInfo.CreateNoWindow = true;
            startInfo.WindowStyle = ProcessWindowStyle.Hidden;
            startInfo.EnvironmentVariables["STUDYFORGE_NO_SPLASH"] = "1";
            startInfo.EnvironmentVariables["STUDYFORGE_NO_BROWSER"] = "1";
            coreProcess = Process.Start(startInfo);
        }
        catch (Exception ex)
        {
            ShowError("\uc2e4\ud589 \uc2dc\uc791\uc5d0 \uc2e4\ud328\ud588\uc2b5\ub2c8\ub2e4.", ex.Message);
            return;
        }

        while (!IsDisposed)
        {
            int? readyPort = FindHealthyPort(instanceId);
            if (readyPort != null)
            {
                closingAfterReady = true;
                statusLabel.Text = "\ube0c\ub77c\uc6b0\uc800 \uc5ec\ub294 \uc911";
                detailLabel.Text = "\uc900\ube44\uac00 \ub05d\ub0ac\uc2b5\ub2c8\ub2e4.";
                OpenUrl(readyPort.Value);
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
                statusLabel.Text = "\uc900\ube44 \uc911";
                detailLabel.Text = "\ucc98\uc74c \uc2e4\ud589\uc774\ub77c \uc870\uae08 \ub354 \uac78\ub9b4 \uc218 \uc788\uc2b5\ub2c8\ub2e4.";
            }

            await Task.Delay(350);
        }
    }

    private async Task<bool> WaitForFileAsync(string path, int timeoutMilliseconds)
    {
        DateTime deadline = DateTime.UtcNow.AddMilliseconds(timeoutMilliseconds);
        while (DateTime.UtcNow < deadline)
        {
            if (File.Exists(path))
            {
                return true;
            }
            await Task.Delay(350);
        }
        return File.Exists(path);
    }

    private static void OpenUrl(int port)
    {
        if (Environment.GetEnvironmentVariable("STUDYFORGE_NO_BROWSER") == "1")
        {
            return;
        }
        try
        {
            string url = "http://127.0.0.1:" + port + "/?sf_launch=" + DateTime.UtcNow.Ticks.ToString();
            Process.Start(new ProcessStartInfo(url)
            {
                UseShellExecute = true
            });
        }
        catch
        {
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
        loadingLine.Stop();
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

        using (SolidBrush white = new SolidBrush(Color.FromArgb(245, 244, 239)))
        using (SolidBrush black = new SolidBrush(Color.FromArgb(20, 22, 23)))
        using (Font markFont = new Font("Segoe UI", 24F, FontStyle.Bold, GraphicsUnit.Pixel))
        using (StringFormat format = new StringFormat())
        {
            using (System.Drawing.Drawing2D.GraphicsPath path = new System.Drawing.Drawing2D.GraphicsPath())
            {
                const int radius = 10;
                Rectangle rect = new Rectangle(0, 0, Width, Height);
                path.AddArc(rect.Left, rect.Top, radius * 2, radius * 2, 180, 90);
                path.AddArc(rect.Right - radius * 2 - 1, rect.Top, radius * 2, radius * 2, 270, 90);
                path.AddArc(rect.Right - radius * 2 - 1, rect.Bottom - radius * 2 - 1, radius * 2, radius * 2, 0, 90);
                path.AddArc(rect.Left, rect.Bottom - radius * 2 - 1, radius * 2, radius * 2, 90, 90);
                path.CloseFigure();
                e.Graphics.FillPath(black, path);
            }

            format.Alignment = StringAlignment.Center;
            format.LineAlignment = StringAlignment.Center;
            e.Graphics.DrawString("ES", markFont, white, new RectangleF(0, 0, Width, Height), format);
        }
    }
}

internal sealed class LoadingLine : Control
{
    private readonly Timer timer;
    private int frame;

    public LoadingLine()
    {
        DoubleBuffered = true;
        timer = new Timer();
        timer.Interval = 45;
        timer.Tick += delegate
        {
            frame = (frame + 1) % 120;
            Invalidate();
        };
        timer.Start();
    }

    public void Stop()
    {
        timer.Stop();
        Visible = false;
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            timer.Dispose();
        }
        base.Dispose(disposing);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        using (SolidBrush track = new SolidBrush(Color.FromArgb(46, 50, 49)))
        using (SolidBrush accent = new SolidBrush(Color.FromArgb(32, 197, 167)))
        {
            e.Graphics.FillRectangle(track, 0, 0, Width, Height);
            int segment = Math.Max(34, Width / 4);
            int x = (int)((Width + segment) * (frame / 119.0)) - segment;
            e.Graphics.FillRectangle(accent, x, 0, segment, Height);
        }
    }
}
