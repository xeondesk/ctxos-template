# CtxOS Frontend

## Overview

This is the React/TypeScript frontend for the CtxOS intelligence platform. It provides a modern, responsive interface for managing context graphs, scoring engines, AI agents, and risk analysis.

## Technology Stack

- **React 18** - UI framework with hooks and concurrent features
- **TypeScript** - Type safety and better developer experience
- **Tailwind CSS** - Utility-first CSS framework for rapid styling
- **Vite** - Fast build tool and development server
- **React Router v6** - Client-side routing
- **Zustand** - Lightweight state management
- **React Query (TanStack Query)** - Data fetching and caching
- **Axios** - HTTP client for API communication
- **Heroicons** - Beautiful SVG icons
- **Recharts** - Data visualization charts
- **React Flow** - Graph visualization and interaction

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.tsx      # Main app layout with sidebar
│   ├── AuthLayout.tsx  # Authentication layout
│   ├── StatCard.tsx    # Dashboard stat cards
│   ├── RiskChart.tsx   # Risk distribution charts
│   ├── RecentActivity.tsx # Activity feed component
│   ├── TopRisks.tsx    # Top risks display
│   ├── GraphVisualization.tsx # Graph visualization
│   ├── EntityDetails.tsx # Entity details panel
│   ├── FilterPanel.tsx # Filter controls
│   ├── GraphControls.tsx # Graph manipulation controls
│   ├── RiskHeatmap.tsx # Risk heatmap visualization
│   ├── RiskDetails.tsx # Risk details panel
│   └── index.ts         # Component exports
├── pages/              # Page components
│   ├── LoginPage.tsx   # Authentication page
│   ├── DashboardPage.tsx # Main dashboard
│   ├── GraphExplorerPage.tsx # Graph exploration
│   ├── RiskHeatmapPage.tsx # Risk heatmap view
│   ├── EntitiesPage.tsx # Entity management
│   ├── ScoringPage.tsx # Scoring interface
│   ├── AgentsPage.tsx # AI agent management
│   └── ConfigurationPage.tsx # System configuration
├── store/              # State management
│   ├── authStore.ts    # Authentication state
│   └── index.ts        # Store exports
├── api/                # API client
│   └── index.ts        # Axios configuration and methods
├── types/              # TypeScript type definitions
│   └── index.ts        # API and UI type definitions
├── App.tsx             # Main app component with routing
├── index.tsx           # Application entry point
└── index.css           # Global styles and Tailwind imports
```

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.9+ (for backend API)

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. The frontend will be available at `http://localhost:3000`

4. Make sure the backend API is running at `http://localhost:8000`

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint
- `npm run type-check` - Run TypeScript type checking

## Features

### Authentication
- Login/logout functionality
- JWT token management
- Role-based access control (RBAC)
- Protected routes

### Dashboard
- Real-time statistics and metrics
- Risk distribution charts
- Recent activity feed
- Top risk entities
- System health monitoring

### Graph Explorer
- Interactive graph visualization
- Entity relationships and connections
- Filtering and search capabilities
- Multiple layout options
- Entity details panel

### Risk Heatmap
- Visual risk assessment grid
- Risk severity indicators
- Impact vs likelihood matrix
- Detailed risk information
- Export capabilities

### Entity Management
- Entity listing and search
- Entity details and metadata
- Relationship visualization
- Bulk operations

### Scoring Interface
- Run scoring engines
- View scoring results
- Historical analysis
- Performance metrics

### AI Agents
- Agent management interface
- Pipeline execution
- Results visualization
- Performance monitoring

### Configuration
- System settings
- Scoring rules management
- User administration
- Audit logs

## API Integration

The frontend is configured to communicate with the backend API at `http://localhost:8000`. All API calls are handled through the centralized API client in `src/api/index.ts`, which includes:

- Automatic authentication headers
- Error handling and retry logic
- Request/response interceptors
- Type-safe API methods

## State Management

State is managed using Zustand stores:

- `authStore` - Authentication state and user information
- Additional stores can be added for other domains

## Styling

The UI uses Tailwind CSS for styling with custom components defined in `src/index.css`. The design system includes:

- Consistent color palette
- Responsive design patterns
- Component variants
- Dark mode support (ready for implementation)

## Development Notes

### TypeScript Configuration

The project uses strict TypeScript configuration with path aliases:
- `@/` maps to `src/` directory
- All components are fully typed

### Code Quality

- ESLint configuration for code consistency
- Prettier for code formatting
- TypeScript strict mode enabled
- Component prop interfaces defined

### Performance

- React.memo for component optimization
- Lazy loading for large components
- Efficient state management
- Optimized bundle size

## Testing

The project is set up for testing with Jest and React Testing Library (to be implemented).

## Deployment

The build process creates optimized production assets in the `dist/` directory, ready for deployment to any static hosting service.

## Contributing

1. Follow the existing code patterns and conventions
2. Use TypeScript for all new code
3. Add proper type definitions
4. Include component documentation
5. Test thoroughly before submitting changes
