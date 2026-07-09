# Tax Policy Monitor Widget

A compact, embeddable widget that watches tax-policy pages and shows the newest stories from:

- Cato
- CBPP
- EPI
- ITEP
- Tax Foundation
- Tax Policy Center
- Yale Budget Lab

It is designed for GitHub Pages and costs $0 to host. GitHub Actions scrapes the sites once an hour and updates `docs/stories.json`.

## What it looks like

The widget shows:

- newest 10 stories
- NEW indicator since your last visit
- source badges
- source filter
- compact search
- dark mode support
- auto-refresh every 5 minutes

## Upload through the GitHub website

1. Download and unzip this project.
2. Create a new GitHub repository, such as `tax-policy-widget`.
3. Open the repository's **Code** tab.
4. Click **Add file → Upload files**.
5. Drag the **contents** of this folder into the upload area.
6. Make sure these paths appear in GitHub:

```text
.github/workflows/update-stories.yml
scripts/scrape.py
docs/index.html
docs/widget.js
docs/styles.css
docs/stories.json
sources.yml
requirements.txt
```

7. Click **Commit changes**.

## Enable GitHub Pages

1. Go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Save.

## Run the scraper once

1. Go to **Actions**.
2. Click **Update Tax Policy Stories**.
3. Click **Run workflow**.
4. Wait for it to finish.

Your site will deploy to:

```text
https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/
```

## Embed the widget

Use an iframe:

```html
<iframe
  src="https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/"
  width="420"
  height="720"
  style="border:0;border-radius:16px;"
  loading="lazy">
</iframe>
```

Or use the tiny embed script:

```html
<script
  src="https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/embed.js"
  data-height="720"
  data-width="420px">
</script>
```

## Customize sources

Edit `sources.yml`. Keep spaces, not tabs. After committing a change, run the workflow again.

## Troubleshooting

If only one or two sources show up, open the latest workflow run and read the scrape log. Some websites change markup or block automated requests. Errors are also written into `docs/stories.json` under the `errors` field.

If Actions says no workflow exists, your `.github/workflows/update-stories.yml` file was not uploaded. Upload the `.github` folder through the GitHub website.
