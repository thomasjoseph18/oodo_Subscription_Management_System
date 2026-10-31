DESIGN.md: Odoo marketing website
Design system reference for odoo.com, reverse-engineered on 2026-10-31 from the homepage HTML and the production stylesheet (web.assets_frontend.min.css).

How to read this file. Token values, type sizes and component rules come straight from the production CSS. Anything marked (inferred) is a reading of the markup, not a confirmed rendered value: the page was never viewed in a browser, so no screenshots or computed styles were checked.

1. Design character
Odoo sells a large enterprise product with the voice of a friendly small business. The design gets there by pairing a sober, Bootstrap-based interface with hand-drawn gestures.

Plain structure, human accents. The layout is a conventional centered grid. The personality comes from a handwritten display face, marker-style highlights and doodle arrows.
Calm color, one brand hue. Mostly white and light gray with near-black text. Aubergine purple is reserved for primary actions and links.
The product is the imagery. App icons, product screens and real customer quotes do the work instead of stock photography.
Direct, price-forward messaging. The price and "free" appear in the hero, not behind a click.
2. Color
Brand and theme
Token	Hex	Use
--o-color-1 / --primary	#714B67	Primary buttons, links, doodle text
--o-color-2 / --secondary	#017E84	Secondary buttons, teal accent
--o-color-3 / --light	#F8F9FA	Light surfaces, footer background
--o-color-4	#FFFFFF	Page background, cards
--o-color-5 / --dark	#111827	Headings, app labels, dark surfaces
Primary states
State	Primary	Secondary
Default	#714B67	#017E84
Hover background	#604058	#016B70
Hover border	#5A3C52	#01656A
Active background	#5A3C52	#01656A
Active border	#55384D	#015F63
Link: #714B67 (#65435C in the cc1 color scheme, #5F3F56 in cc2)
Link hover: #432C3D
Link on dark surfaces: #00A09D
Focus ring: rgba(113, 75, 103, 0.25)
Neutrals
Token	Hex
--100	#F8F9FA
--200	#F3F4F6
--300	#E6E9ED
--400	#D8DADD
--500	#ADB5BD
--600	#6C757D
--700	#495057
--800	#374151
--900	#111827
Body text: #374151, not black
Headings: #111827
Alternating section background: #F3F4F6 (.bg-200)
Card and accordion border: #D8DADD
Semantic
Role	Hex
Success	#28A745
Info	#17A2B8
Warning	#FFC107
Danger	#DC3545
Accent colors in the stylesheet
These appear often in the CSS, but where each one is used was not traced. Treat them as a playful secondary set and use them sparingly: #03F9E3 bright aqua, #1BB6F9 sky, #FBB130 amber, #FC787D coral, #00CEB3 mint, #62DD8B green.

Color schemes
Website sections use five presets (o_cc1 to o_cc5). Each sets text, headings, links and buttons together, so apply a whole scheme to a section rather than coloring elements one at a time.

Scheme	Text	Link	Primary button
cc1	#111827	#65435C	#714B67
cc2	#111827	#5F3F56	#714B67
cc3	#FFFFFF	#00A09D	#714B67
cc4	#FFFFFF	black	white text, #111827 border
cc5	#FFFFFF	#00A09D	#714B67
Contrast (WCAG, calculated)
Pair	Ratio	Result
White on primary #714B67	7.23:1	AAA
White on secondary #017E84	4.86:1	AA
Primary on #F3F4F6	6.57:1	AA
Body #374151 on white	10.31:1	AAA
Muted #6C757D on white	4.69:1	AA, with little margin
Dark link #00A09D on #111827	5.50:1	AA
#ADB5BD on #F8F9FA	1.97:1	Fails: never use for text on light surfaces
3. Typography
Families
Role	Stack	Weights loaded
Sans (UI, body, headings)	"Inter", "Odoo Unicode Support Noto", sans-serif	300, 400, 500, 600
Script (display)	"Caveat"	700
Mono	SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace	n/a
Icons	FontAwesome, odoo_ui_icons	n/a
Inter and Caveat load from Google Fonts.

Marketing display scale (.x_wd pages)
Display classes render in Caveat 700 inside the .x_wd wrapper. Sizes are fluid below the desktop breakpoint, then cap.

Class	Fluid size	Max	Line height
.display-1	calc(1.675rem + 5.1vw)	5.5rem (88px)	1
.display-2	calc(1.6rem + 4.2vw)	4.75rem (76px)	1
.display-3	calc(1.525rem + 3.3vw)	4rem (64px)	1
.display-4	calc(1.425rem + 2.1vw)	3rem (48px)	1
.display-5	calc(1.325rem + 0.9vw)	2rem (32px)	1.1
.display-6	calc(1.3rem + 0.6vw)	1.75rem (28px)	1.1
Homepage use: h1.display-1 for the hero, h2.display-3 for its subhead, h2.display-2 for section titles, h3.display-1 for the closing call to action.

Base scale
Element	Size	Weight	Line height
h1	3.5rem (56px)	600	1.2
h2	2.75rem (44px)	600	1.2
h3	2rem (32px)	600	1.2
h4	1.5rem (24px)	600	1.2
h5	1.25rem (20px)	600	1.2
h6	1rem (16px)	600	1.2
Body	1rem (16px)	400	1.5
Lead	1.25rem (20px)	300	1.5
Small	0.875em	400	1.5
Marketing pages (.x_wd) are one step larger:

p, ul, ol: 1.25rem
.lead: 1.5rem
b, strong, a: weight 600
Rules
Reserve Caveat for display sizes and doodle notes. Never set body text, labels or buttons in it.
Keep headings to weight 600. The site does not load Inter 700 from Google Fonts.
Script fallback: for Arabic, Japanese, Korean, Thai, Vietnamese and Chinese, display text switches to Inter 600 at line height 1.2, with smaller sizes (.display-1 caps at 4rem). Caveat does not suit these languages, so keep this fallback.
4. Spacing and layout
Spacing
Base unit: 16px (1rem).
*-6 utilities equal 4rem (64px).
The site extends Bootstrap's spacing scale. Sections use py-5, py-lg-7, pt-10 and pb-lg-10, so space grows sharply on desktop.
Feature cards: 2rem padding with 2rem bottom margin.
Standard cards: 1.5rem padding on both axes.
Grid
Breakpoint	Min width
sm	576px
md	768px
lg	992px
xl	1200px
xxl	1400px
Grid: Bootstrap 12-column, gutter 32px.
lg (992px) is the main layout switch, with md next, by number of media queries.
Readable column: col-xl-9 col-xxl-8, centered.
Mobile-specific text is often trimmed: the hero button drops " - It's free" below md.
Page rhythm
Sections alternate between white and #F3F4F6, with #F3F4F6 dominating the homepage. Content is centered on large screens (text-lg-center) and left-aligned on small ones.

5. Shape and elevation
Token	Value
--border-radius-sm	0.5rem (8px)
--border-radius	0.75rem (12px)
--border-radius-lg	1.25rem (20px)
--border-radius-xl	1.5rem (24px)
--border-radius-pill	50rem
--border-width	1px
Shadow	Value
sm	0 0.125rem 0.25rem rgba(0, 0, 0, 0.075)
default	0 0.5rem 1rem rgba(0, 0, 0, 0.1)
lg	0 1rem 3rem rgba(0, 0, 0, 0.175)
Feature cards on the homepage use a 1px border and no shadow, so prefer a border over elevation on flat sections.

6. Components
Buttons
.btn {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1.5;
  border: 1px solid transparent;
  border-radius: 0.4rem;
}
Variant	Background	Text	Use
Primary	#714B67	#FFFFFF	Main action, "Start now - It's free"
Secondary	#017E84	#FFFFFF	Alternative action
Light	#F3F4F6	#714B67	Lower-commitment action, "Meet an advisor"
Outline primary	transparent	#65435C, border to match	Tertiary, fills on hover
Disabled: opacity 0.65.
Focus: 0 0 0 0.25rem ring at 50% of the button's focus color.
Active: inset 0 3px 5px rgba(0, 0, 0, 0.125).
Pair one primary with one light button. The button radius (0.4rem) is intentionally tighter than the card radius (0.75rem).
Header
White background, 12px base font size, fixed on scroll (o_header_fixed, o_affix_enabled).
Background and shadow transition at 0.2s.
Logo: 94 × 30px SVG, left aligned.
Mega-menus for Apps, Industries and Community, each grouped into families. Pricing and Help are plain links.
Right side: Sign in, then a "Try it free" primary button.
A hamburger replaces the menu below lg.
App icon tile (.x_wd_app_entry)
24 tiles: col-4 col-sm-3 col-lg-2, giving 3, 4 and 6 per row.
80px icon with img-thumbnail rounded-1, and a small truncated label in #111827.
Hover: lifts translateY(-0.25rem) with all 0.2s ease-in-out.
Feature card (.s_wd_features_item)
White background, #D8DADD-family 1px border, 12px radius, 2rem padding, h4 title with 1.5rem bottom margin. The title keeps a 75px right margin (inferred: room for a corner visual).

Handwritten highlight (x_wd_*_highlight_*)
The signature element. A hand-drawn mark sits behind or around a key phrase in a headline.

Pattern: x_wd_{color}_highlight_{bold_}{nn}. Colors seen: yellow, blue, red, green. There is also x_wd_corner_highlight_04.
Use one per headline, on the phrase that carries the promise ("one platform.", "affordable!").
The homepage uses seven in total across all its sections.
These are almost certainly SVG background images (inferred), so reuse needs your own drawn assets.
Doodle annotation (.x_wd_doodle)
Caveat 700 in #714B67, size calc(1.325rem + 0.9vw), line height 1.1, centered, usually rotated slightly (rotate-350) with a hand-drawn arrow SVG. Hidden below lg. The hero uses one to point at the price.

Other components
Component	Spec
Form input	0.75rem padding, 1rem text, #111827, 1px border, 0.25rem radius, 0.05s transition
Badge	0.75rem, weight 500, 0.5em 0.8em padding, 0.5rem radius
Accordion	#D8DADD border, active background #F3F4F6, 0.15s transitions
Card	1.5rem padding, #D8DADD border, 12px radius, white background
Footer	#F8F9FA background, #111827 text, link columns, language selector
7. Motion
Purpose	Value
Hover on tiles and small elements	all 0.2s ease-in-out
Header background and shadow	0.2s ease
Form states	0.05s ease-in-out
Accordion	0.15s ease-in-out
Larger reveals and fades	0.5s ease
Scroll entrance (.o_animate)	1s, fade in with direction variants
Keep motion small and functional: short lifts, fades on entry. A <noscript> rule forces animated content visible, so content must never depend on JavaScript to appear. Add a prefers-reduced-motion path for any new scroll animation.

8. Imagery and iconography
App icons: colorful, flat, consistent SVGs, the main visual on the homepage. Source pattern: download.odoocdn.com/icons/{module}/static/description/icon.svg.
UI icons: FontAwesome and odoo_ui_icons.
Illustration: hand-drawn doodle shapes as section decoration (o_illustration_doodle_03) and arrows. Flip arrows for right-to-left languages (o_rtl_flip).
Photography: real people with their names and titles, in testimonials.
Decorative images use alt="" and loading="lazy". App icons have descriptive alt text.
9. Homepage structure
Hero: white, centered. Script headline with highlight, price doodle, primary and light buttons.
App grid: 24 tiles on #F3F4F6 with a doodle background.
Breadth statement: "Imagine a vast collection of business apps at your disposal," with "View all Apps."
Third-party quote: a short quote that reinforces simplicity.
Product quality: "Level up your quality of work" and "Optimized for productivity."
Native AI: automation and research capabilities.
Value grid: "Enterprise software done right," in feature cards.
Social proof: "Join 28 million happy users," then a customer testimonial.
Closing call to action: "Unleash your growth potential," a primary button and "No credit card required."
Footer: link columns, language selector, contact and social links.
The primary call to action repeats at the top and bottom of the page, and in the header throughout.

10. Voice
Short, confident, plain. Sentences often end in a period or exclamation mark in headlines: "All your business on one platform."
Concrete claims over adjectives: a price, "less than 90ms," "28 million happy users."
Remove risk beside the action: "It's free," "No credit card required."
Willing to be playful and to compare directly with large competitors.
Sentence case for headings and buttons.
11. Do and don't
Do

Use one Caveat headline with one highlight per section.
Keep purple to actions and links, on white or #F3F4F6.
Use #374151 for body text and #111827 for headings.
Alternate white and light gray sections, with generous vertical space.
Show the real product and real people.
Don't

Don't set paragraphs, buttons or navigation in Caveat.
Don't stack several highlights or doodles in one view.
Don't introduce heavy shadows or gradients as a default treatment.
Don't use #ADB5BD for text on light surfaces.
Don't use more than one primary button in a group.
12. Starter tokens
:root {
  /* Brand */
  --color-primary: #714b67;
  --color-primary-hover: #604058;
  --color-primary-active: #5a3c52;
  --color-secondary: #017e84;
  --color-secondary-hover: #016b70;
  --color-link: #714b67;
  --color-link-hover: #432c3d;
  --color-focus-ring: rgba(113, 75, 103, 0.25);

  /* Neutrals */
  --color-bg: #ffffff;
  --color-bg-subtle: #f3f4f6;
  --color-surface: #f8f9fa;
  --color-border: #d8dadd;
  --color-text: #374151;
  --color-text-muted: #6c757d;
  --color-heading: #111827;

  /* Type */
  --font-sans: "Inter", sans-serif;
  --font-script: "Caveat", cursive;
  --font-size-body: 1rem;
  --font-size-lead: 1.25rem;
  --line-height-body: 1.5;
  --line-height-heading: 1.2;

  /* Shape */
  --radius-button: 0.4rem;
  --radius-sm: 0.5rem;
  --radius-md: 0.75rem;
  --radius-lg: 1.25rem;
  --radius-xl: 1.5rem;

  /* Elevation */
  --shadow-sm: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
  --shadow-md: 0 0.5rem 1rem rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 1rem 3rem rgba(0, 0, 0, 0.175);

  /* Motion */
  --transition-fast: 0.2s ease-in-out;
  --transition-slow: 0.5s ease;

  /* Layout */
  --grid-gutter: 32px;
}
13. Known gaps
Nothing was checked visually. Odoo's page failed to open in the browser, so this file rests on HTML and CSS only.
Spacing steps 7 and 10, container widths and the highlight artwork were not extracted.
The stylesheet covers many Odoo pages. Some rules in it may not apply to the homepage, including a #03F9E3 primary button variant whose scope was not traced.
Only the homepage was analysed. App, pricing and industry pages may add patterns.
The Odoo name, logo and artwork belong to Odoo. Use this as a study reference, not as a basis for a look-alike site.