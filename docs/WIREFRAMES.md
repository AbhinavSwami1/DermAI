# DermAI - UI Wireframes

Low-fidelity layouts of the implemented screens (desktop). Real screenshots are in the submission folder. The application uses one accent colour, warm neutral greys, flat bordered panels, IBM Plex Sans for text and Source Serif 4 for headings. No emojis, gradients or shadows.

## 1. Landing page (visitor)
```
+--------------------------------------------------------------+
| DermAI                                      Log in | Register |
+--------------------------------------------------------------+
| Skin image analysis for research        | What a result contains|
| H1: See what a classifier predicts ...   | - Predicted condition |
| paragraph                                | - Model score         |
| [Start an analysis]  [Log in]            | - Top three           |
|                                          | - Grad-CAM view       |
|                                          | - Record              |
+--------------------------------------------------------------+
| How it works:  01 Upload | 02 Image check | 03 Analysis | 04 Review |
+--------------------------------------------------------------+
| What it covers            | What it does not do               |
+--------------------------------------------------------------+
| | AI predictions are informational ... (limitation statement) |
+--------------------------------------------------------------+
```

## 2. Sign in / Register
```
+----------------------+
| DermAI               |
| Sign in              |
| Email  [__________]  |
| Password [________]  |
| [ Sign in ]          |
| research-use note    |
+----------------------+
```

## 3. Overview (authenticated)
```
| DermAI | Overview | New Analysis | History | Compare | Staff | Insights |  bell  user  [Log out] |
+-------------------------------------------------------------------------------+
| Page title + one-line description                                             |
+-------------------------------------------------------------------------------+
| Your analyses | Test accuracy | Supported classes | Model version  (summary strip) |
+------------------------------------------------+------------------------------+
| Analyze an image                               | Model information            |
| [ No image selected ]  [Choose image]          | architecture, input size ... |
| quality card (status, blur, brightness, flags) |                              |
| [Analyze image]                                |                              |
| warning prompt: [Continue anyway] [Choose ...] |                              |
| RESULT: class, score, Top-3, time, export,     |                              |
|   model input (preprocessed), Grad-CAM         |                              |
+------------------------------------------------+------------------------------+
```

## 4. Analysis history
```
| From [date] To [date] [Clear filter]                           |
| record card: image name, date, class, score, model version     |
|   [PDF] [CSV] [JSON]   > Case notes and follow-up              |
| ... pagination                                                 |
```

## 5. Compare analyses
```
| [Select first analysis v]      [Select second analysis v]      |
| +-----------------------+      +-----------------------+       |
| | date, image, class,   |      | date, image, class,   |       |
| | score, Top-3, version |      | score, Top-3, version |       |
| +-----------------------+      +-----------------------+       |
| note: saved outputs only; no clinical improvement implied      |
```

## 6. Staff dashboards (Dermatologist / Administrator)
```
| Clinician: total cases | analyses | average score | low-score count |
| predicted class distribution | recent analyses table              |
| Administrator: users | cases | images | analyses | last 7 days       |
| model usage                                                       |
| Patient role: message that the page needs a staff role            |
```
