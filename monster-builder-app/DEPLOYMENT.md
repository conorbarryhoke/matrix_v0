# Deployment Guide

## GitHub Pages Deployment (Recommended)

### Prerequisites
- GitHub account
- Git installed locally (or use GitHub web interface)

### Step-by-Step Instructions

#### Method 1: Using Git Command Line

```bash
# 1. Navigate to the monster-builder-app folder
cd monster-builder-app

# 2. Initialize git repository (if not already)
git init

# 3. Add all files
git add .

# 4. Commit files
git commit -m "Initial commit: D&D Monster Builder app"

# 5. Create repository on GitHub
# Go to https://github.com/new and create a new repository
# Name it something like "dnd-monster-builder"
# DO NOT initialize with README (we already have files)

# 6. Add remote and push
git remote add origin https://github.com/YOUR-USERNAME/dnd-monster-builder.git
git branch -M main
git push -u origin main

# 7. Enable GitHub Pages
# Go to repository Settings → Pages
# Source: Deploy from branch "main"
# Folder: / (root)
# Click Save

# 8. Wait 1-2 minutes and visit:
# https://YOUR-USERNAME.github.io/dnd-monster-builder/
```

#### Method 2: Using GitHub Web Interface

1. **Create a New Repository**:
   - Go to https://github.com/new
   - Name: `dnd-monster-builder`
   - Public or Private (Pages works with both)
   - DO NOT initialize with README
   - Click "Create repository"

2. **Upload Files**:
   - Click "uploading an existing file"
   - Drag and drop ALL files from `monster-builder-app/`:
     - `index.html`
     - `styles.css`
     - `app.js`
     - `model_data.json`
     - `README.md`
   - Commit changes

3. **Enable GitHub Pages**:
   - Go to **Settings** → **Pages**
   - Source: **Deploy from a branch**
   - Branch: **main**
   - Folder: **/ (root)**
   - Click **Save**

4. **Access Your Site**:
   - Wait 1-2 minutes for deployment
   - Visit: `https://YOUR-USERNAME.github.io/dnd-monster-builder/`

---

## Alternative Deployment Options

### 1. Netlify (Easiest)

**Drag & Drop Method**:
1. Go to https://app.netlify.com/drop
2. Drag the `monster-builder-app` folder
3. Your site is live instantly!
4. Get a URL like: `https://random-name-12345.netlify.app`

**Git Method**:
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Deploy
cd monster-builder-app
netlify deploy --prod
```

### 2. Vercel

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd monster-builder-app
vercel --prod
```

### 3. Cloudflare Pages

1. Go to https://pages.cloudflare.com/
2. Connect your GitHub repository
3. Build settings:
   - Build command: (leave empty)
   - Build output directory: `/`
4. Deploy!

### 4. Firebase Hosting

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize
cd monster-builder-app
firebase init hosting

# Deploy
firebase deploy --only hosting
```

### 5. AWS S3 + CloudFront

```bash
# Install AWS CLI
# Configure credentials: aws configure

# Create S3 bucket
aws s3 mb s3://dnd-monster-builder

# Enable static website hosting
aws s3 website s3://dnd-monster-builder \
  --index-document index.html

# Upload files
cd monster-builder-app
aws s3 sync . s3://dnd-monster-builder --acl public-read

# Your site: http://dnd-monster-builder.s3-website-us-east-1.amazonaws.com
```

---

## Local Testing

### Using Python

```bash
cd monster-builder-app
python3 -m http.server 8000
# Visit http://localhost:8000
```

### Using Node.js

```bash
cd monster-builder-app
npx http-server -p 8000
# Visit http://localhost:8000
```

### Using PHP

```bash
cd monster-builder-app
php -S localhost:8000
# Visit http://localhost:8000
```

### Using VS Code Live Server

1. Install "Live Server" extension
2. Right-click `index.html`
3. Select "Open with Live Server"

---

## Custom Domain Setup

### GitHub Pages with Custom Domain

1. **Buy a domain** (from Namecheap, Google Domains, etc.)

2. **Add domain to GitHub**:
   - Repository Settings → Pages
   - Custom domain: `monster-builder.yourdomain.com`
   - Save

3. **Configure DNS** (at your domain provider):
   ```
   Type: CNAME
   Name: monster-builder (or @)
   Value: YOUR-USERNAME.github.io
   ```

4. **Wait for DNS propagation** (up to 24 hours)

5. **Enable HTTPS** (checkbox in GitHub Pages settings)

### Netlify with Custom Domain

1. Site settings → Domain management
2. Add custom domain
3. Follow DNS instructions (usually just a CNAME record)
4. SSL is automatic!

---

## Performance Optimization

### Enable Gzip Compression

For GitHub Pages, this is automatic.

For other hosts, add to `.htaccess`:
```apache
<IfModule mod_deflate.c>
  AddOutputFilterByType DEFLATE text/html text/css application/javascript application/json
</IfModule>
```

### Cache Headers

Add to `.htaccess` or Netlify `_headers` file:
```
/model_data.json
  Cache-Control: public, max-age=31536000

/*.css
  Cache-Control: public, max-age=31536000

/*.js
  Cache-Control: public, max-age=31536000
```

### Minify Files (Optional)

```bash
# Install terser for JS minification
npm install -g terser

# Minify JavaScript
terser app.js -c -m -o app.min.js

# Update index.html to reference app.min.js
```

---

## Troubleshooting Deployment

### GitHub Pages Not Loading

**Issue**: 404 error after deployment
**Solution**:
- Check that `index.html` is in the root of your repository
- Ensure GitHub Pages is enabled in Settings
- Wait 5 minutes and clear browser cache

### CORS Errors

**Issue**: "Failed to load model_data.json"
**Solution**:
- Ensure all files are in the same directory
- Use a proper web server (not `file://` protocol)
- Check browser console for exact error

### Model Not Loading

**Issue**: "Error loading model data"
**Solution**:
- Verify `model_data.json` is present and valid JSON
- Check browser Network tab (F12) to see if file loads
- Ensure path is correct in `app.js`

### Blank Page

**Issue**: Nothing displays
**Solution**:
- Open browser console (F12) for errors
- Check that all files uploaded correctly
- Verify JavaScript is enabled in browser

---

## Post-Deployment Checklist

- [ ] Site loads without errors
- [ ] HP calculation works
- [ ] All buttons functional
- [ ] Stat block generates correctly
- [ ] Copy to clipboard works
- [ ] Random monster generator works
- [ ] Mobile responsive (test on phone)
- [ ] Works in multiple browsers (Chrome, Firefox, Safari)

---

## Updating Your Deployment

### GitHub Pages

```bash
# Make changes to files
git add .
git commit -m "Update monster builder"
git push

# Changes go live in ~1 minute
```

### Netlify Drag & Drop

1. Make changes locally
2. Drag updated folder to Netlify dashboard
3. Replaces previous deployment

### Netlify CLI / Vercel

```bash
# Make changes, then:
netlify deploy --prod
# or
vercel --prod
```

---

## Security Considerations

- ✅ No server-side code (static files only)
- ✅ No user data collection
- ✅ No API keys or secrets
- ✅ All computation client-side
- ✅ No database or backend required

---

## Analytics (Optional)

### Add Google Analytics

Add to `index.html` before `</head>`:

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

---

**Deployment Complete!** 🚀

Your D&D Monster Builder is now live and ready to create legendary creatures!
