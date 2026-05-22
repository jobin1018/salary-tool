import { NavLink } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="border-b bg-background sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-14 items-center justify-between">
          <span className="text-lg font-semibold">Salary Tool</span>
          <div className="flex gap-6">
            <NavLink
              to="/employees"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${isActive ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`
              }
            >
              Employees
            </NavLink>
            <NavLink
              to="/insights"
              className={({ isActive }) =>
                `text-sm font-medium transition-colors ${isActive ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`
              }
            >
              Insights
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  )
}
