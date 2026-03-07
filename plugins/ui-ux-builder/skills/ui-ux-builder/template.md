# UX Plan: [Project Name]

## 1. Requirements Summary

- **Purpose**: [What the app does and why]
- **Target Users**: [Who will use it]
- **Design System**: [Tailwind, Material UI, custom, etc.]
- **Responsive**: [Desktop-first / Mobile-first, supported breakpoints]
- **Key Constraints**: [Any design or technical constraints]

## 2. Page Inventory

| Route | Page Name | Purpose |
|---|---|---|
| [/] | [Home] | [Landing page with overview] |
| [/login] | [Login] | [User authentication] |
| [/dashboard] | [Dashboard] | [Main data overview] |

## 3. Component Hierarchy

### [Page Name]

```
[PageRoot]
├── [Header]
│   ├── [Logo]
│   ├── [Navigation]
│   └── [UserMenu]
├── [MainContent]
│   ├── [SectionA]
│   │   ├── [ComponentA1]
│   │   └── [ComponentA2]
│   └── [SectionB]
│       └── [ComponentB1]
└── [Footer]
```

## 4. Navigation Flow

```
[Login] --> [Dashboard]
              ├── [Page A]
              │     └── [Detail View]
              ├── [Page B]
              └── [Settings]
```

## 5. Interactive Elements

| Element | Page | Type | Behavior |
|---|---|---|---|
| [Login Form] | [Login] | [Form] | [Validates credentials, redirects to dashboard] |
| [Nav Links] | [All] | [Navigation] | [Routes to corresponding page] |
| [Action Button] | [Dashboard] | [Button] | [Triggers primary action] |

## 6. State Management

| State | Where | Display |
|---|---|---|
| [Loading] | [Dashboard data] | [Skeleton placeholders or spinner] |
| [Empty] | [List pages] | [Empty state message with call-to-action] |
| [Error] | [API calls] | [Error banner with retry option] |

## 7. Responsive Breakpoints

| Breakpoint | Width | Layout Changes |
|---|---|---|
| [Desktop] | [>= 1024px] | [Full sidebar, multi-column grid] |
| [Tablet] | [768px - 1023px] | [Collapsed sidebar, 2-column grid] |
| [Mobile] | [< 768px] | [Bottom nav, single column, stacked cards] |

## 8. Validation Checklist

- [ ] All pages render without errors
- [ ] Navigation between pages works correctly
- [ ] All interactive elements are present and functional
- [ ] Forms validate input correctly
- [ ] Loading, empty, and error states display properly
- [ ] Desktop layout matches plan (>= 1024px)
- [ ] Tablet layout matches plan (768px)
- [ ] Mobile layout matches plan (375px)
- [ ] Images and assets load correctly
- [ ] Colors and typography match design system

## 9. Screenshots

| Page | Desktop (1400px) | Tablet (768px) | Mobile (375px) |
|---|---|---|---|
| [Home] | [screenshots/home-desktop.png] | [screenshots/home-tablet.png] | [screenshots/home-mobile.png] |
| [Dashboard] | [screenshots/dash-desktop.png] | [screenshots/dash-tablet.png] | [screenshots/dash-mobile.png] |
