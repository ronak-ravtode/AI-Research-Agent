# Agentic AI Research Assistant --- Frontend Implementation Plan

## 1. Frontend Overview

### Project

**Agentic AI Research Assistant for Autonomous Multi-Step Research and
Analysis**

### Frontend Goal

Build a clean, responsive research dashboard that allows users to:

-   Enter a research question.
-   Select research depth.
-   Start an autonomous research session.
-   Observe the agent's progress in real time.
-   View the generated research plan.
-   Inspect retrieved sources.
-   Inspect extracted evidence.
-   See source-quality scores.
-   See verified and unsupported claims.
-   Review detected conflicts.
-   View confidence scores.
-   Read the final research report.
-   Inspect citations.
-   Access previous research sessions.

The frontend should make the **agentic nature of the system visible**.

The user should be able to understand:

``` text
What did the agent plan?
        ↓
What did it search?
        ↓
What sources did it use?
        ↓
What evidence did it extract?
        ↓
What did it verify?
        ↓
Did it need more research?
        ↓
What conflicts did it find?
        ↓
How confident is each conclusion?
        ↓
What is the final report?
```

------------------------------------------------------------------------

# 2. Recommended Frontend Technology Stack

  --------------------------------------------------------------------------
  Layer                   Technology                 Purpose
  ----------------------- -------------------------- -----------------------
  Framework               React + TypeScript         Main frontend
                                                     application

  Build Tool              Vite                       Fast development/build
                                                     environment

  Styling                 Tailwind CSS               Responsive UI and
                                                     styling

  Component Library       shadcn/ui                  Consistent accessible
                                                     UI components

  Icons                   Lucide React               UI icons

  Routing                 React Router               Application navigation

  Server State            TanStack Query             API requests, caching,
                                                     synchronization

  Local UI State          Zustand or React state     Research UI state and
                                                     preferences

  API Client              Fetch / Axios              Backend communication

  Realtime                EventSource / SSE          Live agent progress

  Charts                  Recharts                   Research metrics and
                                                     confidence
                                                     visualization

  Markdown                react-markdown             Render generated
                                                     reports

  Syntax/Code             react-syntax-highlighter   Optional code blocks in
                                                     reports

  Forms                   React Hook Form            Form handling

  Validation              Zod                        Frontend input
                                                     validation

  Notifications           Sonner                     Toast notifications

  Date Handling           date-fns                   Dates and timestamps

  Testing                 Vitest + React Testing     Unit/component tests
                          Library                    

  E2E Testing             Playwright                 End-to-end testing

  Deployment              Vercel / Netlify /         Frontend hosting
                          equivalent                 
  --------------------------------------------------------------------------

## 3. Frontend Architecture

``` text
                         React Application
                                |
                +---------------+---------------+
                |               |               |
                v               v               v
             Router          Providers        Global UI
                |               |               |
                v               v               v
          Page Components   TanStack Query   Toasts/Modals
                |
        +-------+-------+
        |       |       |
        v       v       v
      Home   Research  History
                |
                v
        Research Dashboard
                |
      +---------+----------+
      |         |          |
      v         v          v
    Plan     Progress    Sources
      |         |          |
      +---------+----------+
                |
                v
             Evidence
                |
                v
        Analysis / Conflicts
                |
                v
          Final Report
                |
                v
            Citations
```

------------------------------------------------------------------------

# 4. Recommended Project Structure

``` text
frontend/
│
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   │
│   ├── routes/
│   │   ├── AppRoutes.tsx
│   │   └── routeConfig.ts
│   │
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── ResearchPage.tsx
│   │   ├── HistoryPage.tsx
│   │   └── NotFoundPage.tsx
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MobileNav.tsx
│   │   │
│   │   ├── research/
│   │   │   ├── ResearchInput.tsx
│   │   │   ├── ResearchDepthSelector.tsx
│   │   │   ├── ResearchProgress.tsx
│   │   │   ├── ResearchPlan.tsx
│   │   │   ├── AgentActivity.tsx
│   │   │   ├── SourceList.tsx
│   │   │   ├── SourceCard.tsx
│   │   │   ├── EvidenceList.tsx
│   │   │   ├── EvidenceCard.tsx
│   │   │   ├── ConflictPanel.tsx
│   │   │   ├── ConfidencePanel.tsx
│   │   │   ├── ResearchMetrics.tsx
│   │   │   └── ResearchStatus.tsx
│   │   │
│   │   ├── report/
│   │   │   ├── ReportViewer.tsx
│   │   │   ├── ReportHeader.tsx
│   │   │   ├── ReportSection.tsx
│   │   │   ├── CitationBadge.tsx
│   │   │   └── ReferencesList.tsx
│   │   │
│   │   ├── history/
│   │   │   ├── HistoryList.tsx
│   │   │   ├── HistoryCard.tsx
│   │   │   └── HistoryFilters.tsx
│   │   │
│   │   └── common/
│   │       ├── LoadingSpinner.tsx
│   │       ├── ErrorState.tsx
│   │       ├── EmptyState.tsx
│   │       ├── Badge.tsx
│   │       └── ConfirmDialog.tsx
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── researchApi.ts
│   │   ├── historyApi.ts
│   │   └── reportApi.ts
│   │
│   ├── hooks/
│   │   ├── useResearch.ts
│   │   ├── useResearchStream.ts
│   │   ├── useSources.ts
│   │   ├── useReport.ts
│   │   └── useHistory.ts
│   │
│   ├── store/
│   │   └── researchStore.ts
│   │
│   ├── types/
│   │   ├── research.ts
│   │   ├── source.ts
│   │   ├── evidence.ts
│   │   └── report.ts
│   │
│   ├── lib/
│   │   ├── utils.ts
│   │   ├── constants.ts
│   │   └── validators.ts
│   │
│   └── styles/
│       └── globals.css
│
├── public/
│   └── ...
│
├── .env.example
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

------------------------------------------------------------------------

# 5. Main User Journey

The primary user flow should be:

``` text
Home
 ↓
Enter Research Question
 ↓
Select Research Depth
 ↓
Start Research
 ↓
Research Dashboard
 ↓
Watch Agent Progress
 ↓
View Plan
 ↓
View Sources
 ↓
View Evidence
 ↓
View Verification
 ↓
View Conflicts
 ↓
View Analysis
 ↓
Read Final Report
 ↓
Inspect Citations
 ↓
Save/View Research History
```

The entire application should revolve around this workflow.

------------------------------------------------------------------------

# 6. Page Structure

## 6.1 Home Page

Purpose:

Introduce the system and start research.

Main elements:

``` text
+----------------------------------------------------+
| AI Research Assistant                              |
|                                                    |
| Research anything. Let AI investigate it.          |
|                                                    |
| +------------------------------------------------+ |
| | What do you want to research?                  | |
| |                                                | |
| | Enter your research question...                | |
| +------------------------------------------------+ |
|                                                    |
| Research Depth                                     |
| [ Quick ] [ Standard ] [ Deep ]                   |
|                                                    |
|             [ Start Research ]                    |
+----------------------------------------------------+
```

Add example prompts:

``` text
Try:
• Impact of AI on software development
• Future of renewable energy
• Cybersecurity risks of generative AI
```

Clicking an example should populate the input.

------------------------------------------------------------------------

# 7. Research Input Component

Create:

``` text
components/research/ResearchInput.tsx
```

Responsibilities:

-   Text input/textarea.
-   Character limit.
-   Submit action.
-   Validation.
-   Example queries.
-   Research depth selection.
-   Loading state.

Validation:

``` text
Minimum: 10 characters
Maximum: reasonable application limit
Cannot be empty
```

Error:

``` text
Please enter a meaningful research question.
```

------------------------------------------------------------------------

# 8. Research Depth Selector

Three modes:

### Quick

``` text
3–5 sources
Fast research
```

### Standard

``` text
8–15 sources
Balanced research
Recommended
```

### Deep

``` text
15–25 sources
More extensive research
```

The frontend sends:

``` json
{
  "query": "...",
  "depth": "standard"
}
```

to the backend.

------------------------------------------------------------------------

# 9. Research Dashboard

This is the most important page.

Suggested layout:

``` text
+-------------------------------------------------------------+
| Research: Impact of AI on Software Development              |
| Status: Researching...                                      |
+-------------------------------------------------------------+
|                                                             |
|  Progress                                                   |
|  ● Plan → ● Search → ● Extract → ○ Verify → ○ Analyze     |
|                                                             |
+----------------------+--------------------------------------+
| Agent Activity       | Research Plan                        |
|                      |                                      |
| ✓ Planner            | 1. Find productivity studies        |
| ✓ Researcher         | 2. Find developer surveys           |
| ⟳ Extractor          | 3. Find limitations                  |
| ○ Verifier           | 4. Compare findings                  |
|                      |                                      |
+----------------------+--------------------------------------+
|                                                             |
| Sources | Evidence | Conflicts | Analysis | Report          |
|                                                             |
+-------------------------------------------------------------+
```

------------------------------------------------------------------------

# 10. Research Status

Represent backend states visually:

``` text
planning
researching
extracting
verifying
analyzing
writing
completed
failed
```

Example:

``` text
● Planning
✓ Researching
✓ Extracting
⟳ Verifying
○ Analyzing
○ Writing
```

Do not rely only on color. Include:

-   Icon
-   Label
-   Status text

This improves accessibility.

------------------------------------------------------------------------

# 11. Real-Time Agent Activity

Use SSE from:

``` http
GET /api/research/{id}/stream
```

Create:

``` text
hooks/useResearchStream.ts
```

Example event:

``` json
{
  "agent": "researcher",
  "status": "searching",
  "message": "Searching for recent studies..."
}
```

Display:

``` text
09:32:10  ✓ Planner
Created 5 research tasks

09:32:12  ✓ Researcher
Searching for developer productivity studies

09:32:16  ✓ Researcher
Found 8 candidate sources

09:32:20  ⟳ Extractor
Extracting evidence
```

This is one of the most important UI elements because it proves to the
evaluator that the system is performing a multi-step workflow.

------------------------------------------------------------------------

# 12. Research Plan Component

Create:

``` text
ResearchPlan.tsx
```

Display:

``` text
Research Objective
Evaluate the impact of AI on software development.

Tasks

✓ 1. Find productivity studies
✓ 2. Find developer surveys
⟳ 3. Research limitations
○ 4. Compare findings
○ 5. Generate conclusion
```

Each task can contain:

-   Status
-   Priority
-   Agent responsible
-   Result summary

------------------------------------------------------------------------

# 13. Sources Page/Panel

Create:

``` text
SourceList.tsx
SourceCard.tsx
```

Each source card:

``` text
┌─────────────────────────────────────────────┐
│ AI and Developer Productivity               │
│ example.com                                 │
│                                             │
│ Relevance       92%                         │
│ Reliability     88%                         │
│ Published       2026                        │
│ Type            Research Paper              │
│                                             │
│ [ Open Source ] [ View Evidence ]           │
└─────────────────────────────────────────────┘
```

Add filtering:

``` text
All
Academic
Government
Industry
News
Other
```

Sort by:

``` text
Relevance
Reliability
Recency
```

------------------------------------------------------------------------

# 14. Evidence Interface

The user should be able to see how the system reached conclusions.

Example:

``` text
Claim

"AI-assisted coding reduced task completion time
in the evaluated study."

Evidence

"Participants completed the assigned tasks faster
when using the AI-assisted coding tool."

Source

Research Paper #4

Verification

✓ Supported

Confidence

91%
```

This is much stronger than displaying only the final answer.

------------------------------------------------------------------------

# 15. Verification UI

Create verification badges:

``` text
✓ Supported
≈ Partially Supported
? Unsupported
⚠ Contradicted
```

Example:

``` text
Claim #12

AI tools improve developer productivity.

✓ Supported

Supporting sources: 5
Conflicting sources: 1
Confidence: 84%
```

------------------------------------------------------------------------

# 16. Conflict Detection UI

When conflicts exist, show them prominently.

Example:

``` text
⚠ Conflicting Evidence

Claim:
AI-assisted development improves productivity.

Source A:
+30% productivity

Source B:
+10% productivity

Possible explanation:
Different study methodologies and participant groups.

[ View Sources ]
```

Do not hide conflicts inside the report.

------------------------------------------------------------------------

# 17. Confidence Panel

Show overall and claim-level confidence.

Example:

``` text
Research Confidence

             86%
        High Confidence

Supporting Sources     12
Verified Claims        31
Conflicts                2
Unsupported Claims      1
```

Use a chart only where it improves comprehension.

Possible Recharts components:

-   Radial/bar chart for confidence.
-   Bar chart for source quality.
-   Small metrics cards for research statistics.

Avoid decorative charts with no analytical value.

------------------------------------------------------------------------

# 18. Research Metrics

Display:

``` text
Sources Retrieved       18
Sources Accepted        13
Claims Extracted        37
Claims Verified         31
Conflicts Detected       2
Research Iterations      2
Research Time          42s
Citation Coverage       94%
```

This makes the system measurable and useful during the viva.

------------------------------------------------------------------------

# 19. Final Report Viewer

Create:

``` text
components/report/ReportViewer.tsx
```

Report layout:

``` text
-------------------------------------------------
Research Report

Impact of AI on Software Development

Executive Summary
...

Research Question
...

Methodology
...

Key Findings
...

Comparative Analysis
...

Conflicting Evidence
...

Confidence Assessment
...

Conclusion
...

References
...
-------------------------------------------------
```

Use `react-markdown` for rendering Markdown generated by the backend.

------------------------------------------------------------------------

# 20. Citation UI

Citations should be clickable.

Example:

``` text
AI-assisted programming can improve productivity [4].
```

Click `[4]`:

``` text
┌─────────────────────────────────────────┐
│ Citation #4                             │
│                                         │
│ AI Developer Productivity Study         │
│ Research Organization                   │
│ 2026                                    │
│                                         │
│ Why it was used                         │
│ Supports the productivity finding.      │
│                                         │
│ [ Open Source ]                         │
└─────────────────────────────────────────┘
```

The citation interface should map directly to backend source IDs.

------------------------------------------------------------------------

# 21. References Section

Example:

``` text
References

[1] Research Organization — AI Productivity Study
[2] Government Report — AI and Software Engineering
[3] Industry Survey — Developer AI Adoption
[4] Academic Study — AI-Assisted Programming

[Open Source]
```

Avoid displaying raw URLs throughout the report.

------------------------------------------------------------------------

# 22. Research History Page

Create:

``` text
pages/HistoryPage.tsx
```

Display:

``` text
Research History

+-----------------------------------------------+
| AI impact on software development             |
| Completed • 18 sources • 42 seconds           |
| September 10, 2026                             |
|                              [Open Research]   |
+-----------------------------------------------+

+-----------------------------------------------+
| Cybersecurity risks of Generative AI          |
| Completed • 21 sources • 51 seconds           |
| September 9, 2026                              |
|                              [Open Research]   |
+-----------------------------------------------+
```

Filters:

``` text
All
Completed
Failed
In Progress
```

Optional search:

``` text
Search research history...
```

------------------------------------------------------------------------

# 23. API Integration Layer

Do not call APIs directly inside UI components.

Use:

``` text
api/
├── client.ts
├── researchApi.ts
├── historyApi.ts
└── reportApi.ts
```

Example:

``` typescript
export async function startResearch(payload: StartResearchRequest) {
  return api.post("/api/research", payload);
}
```

Then React hooks call the API layer.

This keeps the frontend maintainable.

------------------------------------------------------------------------

# 24. TanStack Query

Use TanStack Query for server state.

Examples:

``` text
useResearch()
useSources()
useReport()
useHistory()
```

Responsibilities:

-   API caching.
-   Loading states.
-   Error states.
-   Refetching.
-   Query invalidation.

Do not put all API data into Zustand.

Use Zustand only for genuine client/UI state.

------------------------------------------------------------------------

# 25. Research Store

Possible Zustand state:

``` typescript
{
  activeResearchId: string | null,
  selectedTab: "overview" | "sources" | "evidence" | "report",
  selectedSourceId: string | null,
  selectedClaimId: string | null,
  researchDepth: "quick" | "standard" | "deep"
}
```

Backend data should remain managed by TanStack Query.

------------------------------------------------------------------------

# 26. TypeScript Types

Create shared frontend types.

Example:

``` typescript
type ResearchStatus =
  | "planning"
  | "researching"
  | "extracting"
  | "verifying"
  | "analyzing"
  | "writing"
  | "completed"
  | "failed";
```

Source:

``` typescript
interface Source {
  id: string;
  title: string;
  url: string;
  domain: string;
  sourceType: string;
  relevanceScore: number;
  reliabilityScore: number;
}
```

Evidence:

``` typescript
interface Evidence {
  id: string;
  sourceId: string;
  claim: string;
  evidenceText: string;
  confidenceScore: number;
  verificationStatus: string;
}
```

------------------------------------------------------------------------

# 27. Loading States

Every asynchronous component needs a proper loading state.

Examples:

``` text
Loading research...
Loading sources...
Generating report...
```

For research execution, use meaningful agent progress instead of a
generic spinner.

Bad:

``` text
Loading...
```

Better:

``` text
Researching sources...
12 sources discovered
Analyzing evidence...
```

------------------------------------------------------------------------

# 28. Error States

Possible errors:

``` text
Research failed
Search service unavailable
Report generation failed
Research session not found
Connection interrupted
```

Example:

``` text
Research interrupted

The connection to the research agent was lost.

[ Retry ] [ Return Home ]
```

Don't show raw backend stack traces to users.

------------------------------------------------------------------------

# 29. SSE Connection Handling

Handle:

``` text
Connected
Disconnected
Reconnected
Completed
Failed
```

If the connection drops:

``` text
Connection interrupted.
Reconnecting...
```

After research completion:

``` text
EventSource.close()
```

Avoid leaving SSE connections open unnecessarily.

------------------------------------------------------------------------

# 30. Responsive Design

The application must work on:

``` text
Desktop
Tablet
Mobile
```

Desktop:

``` text
Sidebar + Main Dashboard
```

Mobile:

``` text
Top Header
Tabs
Single-column cards
Bottom/mobile navigation if required
```

Don't simply shrink the desktop dashboard.

The information hierarchy should change for smaller screens.

------------------------------------------------------------------------

# 31. Design System

Use a consistent design system.

### Typography

Use:

``` text
Inter / Geist / system font
```

Hierarchy:

``` text
Page title
Section title
Card title
Body
Metadata
```

### Components

Use shadcn/ui for:

``` text
Button
Card
Tabs
Badge
Dialog
Dropdown
Tooltip
Progress
Accordion
Skeleton
Toast
```

------------------------------------------------------------------------

# 32. Color Semantics

Use color consistently:

``` text
Neutral → Information
Blue → Processing
Green → Verified / Completed
Yellow → Warning / Partial
Red → Error / Contradiction
```

But never communicate status through color alone.

For example:

``` text
✓ Verified
⚠ Conflict
✕ Failed
```

------------------------------------------------------------------------

# 33. Accessibility

Implement:

-   Semantic HTML.
-   Keyboard navigation.
-   Visible focus states.
-   Accessible buttons.
-   ARIA labels where needed.
-   Sufficient text contrast.
-   Do not use color as the only status indicator.
-   Proper heading hierarchy.

Research reports should be readable by screen readers.

------------------------------------------------------------------------

# 34. URL and Navigation Design

Suggested routes:

``` text
/
                 Home

/research/:id
                 Active research dashboard

/research/:id/sources
                 Sources

/research/:id/evidence
                 Evidence

/research/:id/report
                 Final report

/history
                 Research history
```

You can also keep Sources/Evidence/Report as tabs within `/research/:id`
if simpler.

For a four-week project, tabs inside the research dashboard are
preferable.

------------------------------------------------------------------------

# 35. Frontend Environment Variables

`.env.example`:

``` env
VITE_API_BASE_URL=http://localhost:8000
```

Production:

``` env
VITE_API_BASE_URL=https://your-backend-domain
```

Never put:

``` text
GROQ_API_KEY
TAVILY_API_KEY
FIRECRAWL_API_KEY
```

in the frontend.

Those belong only on the backend.

------------------------------------------------------------------------

# 36. API Data Flow

## Start Research

``` text
ResearchInput
     ↓
useResearch()
     ↓
POST /api/research
     ↓
research_id
     ↓
Navigate to /research/{id}
```

## Monitor Progress

``` text
Research Dashboard
     ↓
useResearchStream()
     ↓
GET /api/research/{id}/stream
     ↓
Agent events
     ↓
Update UI
```

## Get Sources

``` text
GET /api/research/{id}/sources
     ↓
TanStack Query
     ↓
SourceList
```

## Get Report

``` text
GET /api/research/{id}/report
     ↓
TanStack Query
     ↓
ReportViewer
```

------------------------------------------------------------------------

# 37. Research Dashboard State Flow

``` text
Research Started
      ↓
status = planning
      ↓
SSE events
      ↓
status = researching
      ↓
sources update
      ↓
status = extracting
      ↓
evidence update
      ↓
status = verifying
      ↓
verification update
      ↓
status = analyzing
      ↓
conflicts/analysis update
      ↓
status = writing
      ↓
report available
      ↓
status = completed
```

------------------------------------------------------------------------

# 38. Research Dashboard Tabs

Recommended:

``` text
Overview
Sources
Evidence
Analysis
Report
```

### Overview

Show:

-   Query
-   Status
-   Progress
-   Agent activity
-   Research plan
-   Metrics

### Sources

Show:

-   Sources
-   Scores
-   Filters
-   Domains
-   Source types

### Evidence

Show:

-   Claims
-   Evidence
-   Verification
-   Confidence

### Analysis

Show:

-   Key findings
-   Conflicts
-   Confidence
-   Research gaps

### Report

Show:

-   Final report
-   Citations
-   References

------------------------------------------------------------------------

# 39. Empty States

Example:

### No conflicts

``` text
✓ No significant conflicts detected

The available sources were generally consistent.
```

### No evidence

``` text
No evidence available yet.

The research agent is still extracting information.
```

### No history

``` text
No research sessions yet.

Start your first research task.
```

------------------------------------------------------------------------

# 40. Frontend Error Boundaries

Wrap major application areas with error boundaries:

``` text
App
 ├── Layout
 ├── Research Dashboard
 ├── Sources
 └── Report
```

If the report component crashes, the entire application should not
become unusable.

------------------------------------------------------------------------

# 41. Performance Optimization

Do not prematurely optimize.

Use:

-   TanStack Query caching.
-   Lazy-loaded pages.
-   Virtualized lists only if source/evidence lists become large.
-   Debounced history search.
-   Memoization only where profiling shows a need.
-   Avoid rendering huge report content repeatedly.

Do not add unnecessary complexity.

------------------------------------------------------------------------

# 42. Frontend Testing

## Unit Tests

Test:

``` text
ResearchInput
ResearchDepthSelector
StatusBadge
SourceCard
EvidenceCard
ConflictPanel
CitationBadge
```

## Hook Tests

Test:

``` text
useResearch
useResearchStream
useSources
useReport
```

## Integration Tests

Test:

``` text
Research form
 ↓
API call
 ↓
Research page
 ↓
SSE events
 ↓
Report display
```

## E2E Test

Use Playwright:

``` text
Open application
 ↓
Enter research question
 ↓
Select standard depth
 ↓
Start research
 ↓
Wait for completion
 ↓
Verify sources displayed
 ↓
Verify report displayed
 ↓
Verify citation available
```

------------------------------------------------------------------------

# 43. Four-Week Frontend Development Plan

## Week 1 --- UI Foundation

### Day 1

-   Initialize React + TypeScript + Vite.
-   Configure Tailwind CSS.
-   Configure shadcn/ui.
-   Configure routing.
-   Create AppShell.

### Day 2

-   Build Home Page.
-   Build research input.
-   Build research-depth selector.
-   Add example questions.

### Day 3

-   Create API client.
-   Define TypeScript interfaces.
-   Connect start-research endpoint.

### Day 4

-   Build Research Dashboard.
-   Add status component.
-   Add tabs.

### Day 5

-   Integrate TanStack Query.
-   Implement basic loading/error states.
-   Connect research status API.

### Week 1 Target

``` text
Home
 ↓
Research Question
 ↓
Start Research
 ↓
Research Dashboard
```

------------------------------------------------------------------------

# 44. Week 2 --- Agent Visibility

### Day 6

Build:

``` text
Research Plan
Agent Activity
Progress Timeline
```

### Day 7

Implement SSE:

``` text
useResearchStream()
```

### Day 8

Build Sources UI:

``` text
SourceList
SourceCard
Source filters
```

### Day 9

Build Evidence UI:

``` text
EvidenceList
EvidenceCard
Verification badges
```

### Day 10

Connect all components to real backend data.

### Week 2 Target

``` text
Research
 ↓
Live Agent Progress
 ↓
Plan
 ↓
Sources
 ↓
Evidence
```

------------------------------------------------------------------------

# 45. Week 3 --- Intelligence UI

### Day 11

Build:

``` text
Analysis panel
Key findings
```

### Day 12

Build:

``` text
Conflict Detection UI
```

### Day 13

Build:

``` text
Confidence Panel
Research Metrics
```

### Day 14

Build:

``` text
Citation UI
References
Source detail modal
```

### Day 15

Build:

``` text
Final Report Viewer
```

### Week 3 Target

``` text
Evidence
 ↓
Verification
 ↓
Conflicts
 ↓
Confidence
 ↓
Citations
 ↓
Report
```

------------------------------------------------------------------------

# 46. Week 4 --- History, Polish and Testing

### Day 16

Build:

``` text
Research History
History Cards
History filters
```

### Day 17

Responsive design:

``` text
Desktop
Tablet
Mobile
```

### Day 18

Accessibility and UX improvements.

### Day 19

Testing:

``` text
Unit tests
Integration tests
E2E tests
```

### Day 20

Final integration:

``` text
Frontend
 ↓
Backend
 ↓
SSE
 ↓
Research
 ↓
Report
```

Then:

-   Fix bugs.
-   Optimize loading.
-   Test failed research scenarios.
-   Prepare screenshots.
-   Prepare demo.
-   Prepare viva.

------------------------------------------------------------------------

# 47. Component Development Order

Build components in this order:

``` text
1. AppShell
2. HomePage
3. ResearchInput
4. ResearchDepthSelector
5. API Client
6. Research Dashboard
7. Status / Progress
8. Research Plan
9. SSE Activity
10. Source List
11. Source Card
12. Evidence List
13. Evidence Card
14. Verification UI
15. Conflict Panel
16. Confidence Panel
17. Metrics
18. Citation UI
19. Report Viewer
20. History
21. Responsive Design
22. Testing
```

------------------------------------------------------------------------

# 48. Important UX Principle

The user should always know:

``` text
What is happening?
Why is it happening?
What has been found?
What remains?
Is the result trustworthy?
```

For example, instead of:

``` text
Generating...
```

show:

``` text
Analyzing 31 verified claims
Comparing evidence from 13 sources
2 conflicting findings detected
```

This makes the agent feel transparent and purposeful.

------------------------------------------------------------------------

# 49. What NOT to Build

For the four-week project, avoid:

-   Complex admin dashboard.
-   Voice interface.
-   Mobile application.
-   Social features.
-   Chat-style interface as the primary UI.
-   Dozens of animations.
-   Excessive charts.
-   Multiple frontend frameworks.
-   Complex drag-and-drop workflow builder.
-   User customization that does not support research.
-   Fake agent reasoning visualizations.

The goal is **research transparency**, not visual complexity.

------------------------------------------------------------------------

# 50. Recommended Final UI

``` text
┌──────────────────────────────────────────────────────────────┐
│ AI RESEARCH ASSISTANT                         History   ⚙     │
├───────────────┬──────────────────────────────────────────────┤
│               │                                              │
│ NEW RESEARCH  │  Impact of AI on Software Development       │
│               │                                              │
│ History       │  ● Planning ✓  ● Research ✓  ⟳ Analysis     │
│               │                                              │
│ Settings      ├──────────────────────────────────────────────┤
│               │                                              │
│               │  OVERVIEW | SOURCES | EVIDENCE | ANALYSIS   │
│               │           | REPORT                          │
│               │                                              │
│               │  ┌─────────────────┐ ┌────────────────────┐ │
│               │  │ Agent Activity  │ │ Research Plan      │ │
│               │  │                 │ │                    │ │
│               │  │ ✓ Planner       │ │ ✓ Task 1           │ │
│               │  │ ✓ Researcher    │ │ ✓ Task 2           │ │
│               │  │ ⟳ Verifier      │ │ ⟳ Task 3           │ │
│               │  └─────────────────┘ └────────────────────┘ │
│               │                                              │
│               │  Sources: 13   Claims: 31   Conflicts: 2   │
│               │  Confidence: 86%                             │
│               │                                              │
└───────────────┴──────────────────────────────────────────────┘
```

------------------------------------------------------------------------

# 51. Final Frontend Deliverables

## Pages

``` text
Home
Research Dashboard
History
404
```

## Research Dashboard

``` text
Overview
Sources
Evidence
Analysis
Report
```

## Core Components

``` text
Research Input
Research Depth Selector
Progress Tracker
Agent Activity
Research Plan
Source List
Source Card
Evidence List
Evidence Card
Verification Badge
Conflict Panel
Confidence Panel
Research Metrics
Citation Badge
Report Viewer
References
History Card
```

## Frontend Capabilities

``` text
✓ Start research
✓ Select research depth
✓ Monitor autonomous agent
✓ View research plan
✓ View sources
✓ Inspect evidence
✓ Inspect verification
✓ Detect conflicts
✓ View confidence
✓ View metrics
✓ Read report
✓ Follow citations
✓ View research history
✓ Responsive UI
✓ Error handling
✓ Real-time progress
```

------------------------------------------------------------------------

# 52. Final Frontend-to-Backend Contract

``` text
                    FRONTEND
                       |
                       |
                 POST /research
                       |
                       v
                    BACKEND
                       |
                  LangGraph
                       |
              Agentic Research
                       |
                       v
               PostgreSQL
                       |
                       |
              GET /research/:id
                       |
                       v
                    FRONTEND

                 SSE STREAM
                       ↑
                       |
              Agent Progress
                       |
                       |
               Backend Agent
```

The frontend should **never call Groq, Tavily, or Firecrawl directly**.

Correct:

``` text
React
  ↓
FastAPI
  ↓
LangGraph
  ↓
Groq / Tavily / Firecrawl
```

Incorrect:

``` text
React
 ├── Groq
 ├── Tavily
 └── Firecrawl
```

Keeping API keys and agent logic on the backend is essential.

------------------------------------------------------------------------

# 53. Final Frontend Architecture Principle

**React + TypeScript provides the application layer. Tailwind +
shadcn/ui provides the design system. TanStack Query manages backend
state. SSE exposes live agent activity. The UI makes planning,
retrieval, verification, evidence, conflicts, confidence, and report
generation visible.**

The frontend should not pretend to show hidden LLM chain-of-thought. It
should display **observable agent events, decisions, task status,
retrieved sources, evidence, and outputs** that the backend explicitly
exposes.

The primary design objective is:

> **Make the autonomous research process understandable without making
> the interface complicated.**
