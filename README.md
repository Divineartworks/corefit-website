# CoreFit website

**Live: https://corefit-web.pages.dev**

The marketing page for CoreFit, a training app and console for Norwegian gyms. One static
page, written in Norwegian (bokmål): hand-written HTML, CSS and a few lines of JS, no
framework. `build.py` subsets the fonts, makes AVIF/WebP image sets and inlines the CSS
into `dist/`, which is served from Cloudflare Pages.

```sh
pip install pillow fonttools brotli
python build.py
npx wrangler pages deploy dist --project-name=corefit-web --branch=main
```

`BRAND`, `SITE_URL`, `APP_URL`, `CONSOLE_URL` and `CONTACT_EMAIL` are environment
overrides, so a rename is a rebuild, not an edit.

## How it is built

- **Honest copy.** Every claim is something that runs in production today, or sits under
  "Under arbeid" in the status section. No invented customers, quotes or numbers.
- **Real screens.** `assets/screens/` are screenshots of the member app and gym console,
  with a demo member's training history.
- **AI photographs.** `assets/photos/` were generated with Gemini image models. They show
  no real people, carry empty alt text, and the footer says they are AI illustrations.
- **Motion without JS.** Scroll-linked motion uses CSS scroll-driven animations
  (`animation-timeline`) and only touches decoration; text never animates. With reduced
  motion or without support the page is complete and still.
- **Target:** Lighthouse mobile 100 in all four categories, no axe violations, no
  horizontal scroll at 375 px.

Fonts: Inter and Inter Display by Rasmus Andersson, SIL Open Font License 1.1.
