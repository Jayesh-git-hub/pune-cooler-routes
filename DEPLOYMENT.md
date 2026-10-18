# 🌐 Deploying Pune Cooler Routes

You can deploy and use the **Pune Cooler Routes** navigation platform anywhere in the world on any smartphone, tablet, or laptop. Below are the three best methods:

---

## ⚡ Option 1: Instant Live Public URL (Zero-Configuration, Live in 10 Seconds)

If your computer is on, you can make your server accessible globally over a secure HTTPS URL:

1. **Start the backend server:**
   ```bash
   python scripts/day5_server.py 8050
   ```

2. **Open a second terminal and expose it to the internet via HTTPS:**
   ```bash
   npx localtunnel --port 8050
   ```
   *Or with a custom name:*
   ```bash
   npx localtunnel --port 8050 --subdomain pune-cool-routes
   ```

3. **Open the generated URL on your phone or share it with anyone!**
   - Example: `https://pune-cool-routes.loca.lt`
   - It is fully mobile-responsive and secure (HTTPS).

---

## ☁️ Option 2: 24/7 Permanent Free Cloud Deployment on Render (Recommended)

Render provides free hosting directly connected to your GitHub repository:

1. **Sign in to Render:** Go to [render.com](https://render.com) and sign in with your GitHub account (`Jayesh-git-hub`).
2. **Create a New Web Service:**
   - Click **New +** → **Web Service**.
   - Connect your repository: `Jayesh-git-hub/pune-cooler-routes`.
3. **Configuration:**
   - **Environment:** `Python 3`
   - **Region:** Singapore / Frankfurt / Oregon (any)
   - **Branch:** `main`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python scripts/day5_server.py`
   - **Plan:** Free
4. **Click Deploy Web Service:**
   - Render automatically provisions the environment and deploys the app.
   - Your permanent live URL will be: `https://pune-cooler-routes.onrender.com`.

---

## 🚂 Option 3: 1-Click Deployment on Railway (via Docker)

Railway automatically detects our included `Dockerfile`:

1. **Sign in to Railway:** Go to [railway.app](https://railway.app) and sign in with GitHub.
2. **Deploy from GitHub:** Click **New Project** → **Deploy from GitHub repo** → select `pune-cooler-routes`.
3. **Generate Public Domain:**
   - Once deployed, click on the project card → **Settings** → **Networking** → **Generate Domain**.
   - Your site is immediately live with HTTPS.

---

## 📱 Option 4: Installing as a Mobile App (Progressive Web App - PWA)

Once you open the website on your phone:
- **Android (Chrome):** Tap the menu (`⋮`) → **Install app** or **Add to Home screen**.
- **iOS (Safari):** Tap the Share button (`⎋`) → **Add to Home Screen**.
- The app installs to your home screen with a standalone app window, offline map tile caching, and one-tap **"📍 Use My GPS"** navigation.
