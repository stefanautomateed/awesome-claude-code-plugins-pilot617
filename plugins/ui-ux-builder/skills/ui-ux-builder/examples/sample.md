# UX Plan: Support Dashboard

## 1. Requirements Summary

- **Purpose**: Internal support dashboard for tracking customer interactions and resolving tickets
- **Target Users**: Support agents and team leads
- **Design System**: Tailwind CSS with dark theme (slate-900 background, slate-800 cards)
- **Responsive**: Desktop-first with tablet support (>= 768px)
- **Key Constraints**: Must load within 2 seconds, accessible color contrast ratios

## 2. Page Inventory

| Route | Page Name | Purpose |
|---|---|---|
| /login | Login | Agent authentication |
| /dashboard | Dashboard | Overview of metrics, recent activity, queue status |
| /interactions | Interaction List | Searchable, filterable list of all interactions |
| /interactions/:id | Interaction Detail | Full view of a single interaction with timeline |
| /settings | Settings | Agent preferences, notification settings |

## 3. Component Hierarchy

### Dashboard

```
DashboardPage
├── TopNav
│   ├── Logo
│   ├── SearchBar
│   ├── NotificationBell
│   └── UserAvatar
├── Sidebar
│   ├── NavItem (Dashboard)
│   ├── NavItem (Interactions)
│   └── NavItem (Settings)
├── MainContent
│   ├── MetricsRow
│   │   ├── MetricCard (Open Tickets)
│   │   ├── MetricCard (Avg Response Time)
│   │   ├── MetricCard (Resolution Rate)
│   │   └── MetricCard (CSAT Score)
│   ├── RecentActivity
│   │   └── ActivityItem (x N)
│   └── QueueStatus
│       └── QueueRow (x N)
└── Footer
```

### Interaction List

```
InteractionListPage
├── TopNav
├── Sidebar
├── MainContent
│   ├── FilterBar
│   │   ├── SearchInput
│   │   ├── StatusFilter (dropdown)
│   │   ├── DateRangeFilter
│   │   └── AgentFilter (dropdown)
│   ├── InteractionTable
│   │   ├── TableHeader
│   │   └── TableRow (x N)
│   │       ├── StatusBadge
│   │       ├── CustomerName
│   │       ├── Subject
│   │       ├── AssignedAgent
│   │       └── LastUpdated
│   └── Pagination
└── Footer
```

## 4. Navigation Flow

```
Login --> Dashboard
            ├── Interactions
            │     └── Interaction Detail
            │           └── (back to) Interactions
            └── Settings
```

## 5. Interactive Elements

| Element | Page | Type | Behavior |
|---|---|---|---|
| Login Form | Login | Form | Email/password validation, submits to auth API, redirects to Dashboard |
| Search Bar | TopNav | Input | Searches interactions by keyword, debounced 300ms |
| Notification Bell | TopNav | Button | Opens notification dropdown with unread count badge |
| Metric Cards | Dashboard | Display | Clickable, navigates to filtered interaction list |
| Filter Bar | Interaction List | Form | Filters table in real-time, updates URL params |
| Status Filter | Interaction List | Dropdown | Filters by: Open, In Progress, Resolved, Closed |
| Pagination | Interaction List | Navigation | Page size 25, shows total count |
| Reply Button | Interaction Detail | Button | Opens reply editor |
| Status Dropdown | Interaction Detail | Dropdown | Changes interaction status with confirmation |
| Settings Form | Settings | Form | Saves preferences, shows success toast |

## 6. State Management

| State | Where | Display |
|---|---|---|
| Loading | Dashboard metrics | Animated skeleton cards matching card dimensions |
| Loading | Interaction table | Skeleton rows (5 rows) with pulsing animation |
| Empty | Interaction list (filtered) | "No interactions match your filters" with clear-filters button |
| Empty | Recent activity | "No recent activity" with subtle illustration |
| Error | API failures | Red banner at top: "Failed to load data. Retry" with retry button |
| Error | Login failure | Inline error below form: "Invalid credentials" |

## 7. Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|---|---|---|
| Desktop | >= 1024px | Full sidebar (240px), 4-column metric grid, full table columns |
| Tablet | 768px - 1023px | Collapsed sidebar (icons only, 64px), 2-column metric grid, hide Agent column in table |

## 8. Validation Checklist

- [x] All pages render without errors
- [x] Navigation between pages works correctly
- [x] All interactive elements are present and functional
- [x] Forms validate input correctly
- [x] Loading, empty, and error states display properly
- [x] Desktop layout matches plan (>= 1024px)
- [x] Tablet layout matches plan (768px)
- [ ] Mobile layout matches plan (375px) — N/A, not in scope
- [x] Images and assets load correctly
- [x] Colors and typography match design system

## 9. Screenshots

| Page | Desktop (1400px) | Tablet (768px) |
|---|---|---|
| Login | screenshots/login-desktop.png | screenshots/login-tablet.png |
| Dashboard | screenshots/dashboard-desktop.png | screenshots/dashboard-tablet.png |
| Interactions | screenshots/interactions-desktop.png | screenshots/interactions-tablet.png |
| Interaction Detail | screenshots/detail-desktop.png | screenshots/detail-tablet.png |
| Settings | screenshots/settings-desktop.png | screenshots/settings-tablet.png |

## Sample `--structure` Output (Dashboard)

```json
{
  "meta": {
    "title": "Support Dashboard",
    "description": "Internal support dashboard",
    "viewport": "width=device-width, initial-scale=1"
  },
  "headings": [
    {"tag": "h1", "text": "Dashboard"},
    {"tag": "h2", "text": "Metrics Overview"},
    {"tag": "h2", "text": "Recent Activity"},
    {"tag": "h2", "text": "Queue Status"}
  ],
  "buttons": [
    {"text": "View All", "tag": "button", "disabled": false},
    {"text": "Refresh", "tag": "button", "disabled": false},
    {"text": "Export", "tag": "button", "disabled": false}
  ],
  "links": [
    {"text": "Dashboard", "href": "/dashboard"},
    {"text": "Interactions", "href": "/interactions"},
    {"text": "Settings", "href": "/settings"},
    {"text": "Open Tickets (24)", "href": "/interactions?status=open"},
    {"text": "View All Activity", "href": "/interactions?sort=recent"}
  ]
}
```
