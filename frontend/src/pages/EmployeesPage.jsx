import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Pencil, Trash2, Plus } from 'lucide-react'
import { getEmployees, getFilters } from '@/api/employees'
import { useDebounce } from '@/hooks/useDebounce'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import EmployeeModal from '@/components/EmployeeModal'
import DeleteDialog from '@/components/DeleteDialog'

const PAGE_SIZE = 20

const EMP_TYPE_COLORS = {
  'Full-time': 'default',
  'Part-time': 'secondary',
  'Contract': 'outline',
  'Intern': 'secondary',
}

function formatSalary(salary, currency) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(salary)
}

export default function EmployeesPage() {
  const [search, setSearch] = useState('')
  const [country, setCountry] = useState('all')
  const [department, setDepartment] = useState('all')
  const [employmentType, setEmploymentType] = useState('all')
  const [page, setPage] = useState(1)
  const [modalOpen, setModalOpen] = useState(false)
  const [editEmployee, setEditEmployee] = useState(null)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteEmployee, setDeleteEmployee] = useState(null)

  const debouncedSearch = useDebounce(search, 300)

  const params = {
    page,
    page_size: PAGE_SIZE,
    sort_by: 'hire_date',
    sort_order: 'desc',
    ...(debouncedSearch && { search: debouncedSearch }),
    ...(country && country !== 'all' && { country }),
    ...(department && department !== 'all' && { department }),
    ...(employmentType && employmentType !== 'all' && { employment_type: employmentType }),
  }

  const { data, isLoading, isError } = useQuery({
    queryKey: ['employees', params],
    queryFn: () => getEmployees(params),
    keepPreviousData: true,
  })

  const { data: filters } = useQuery({
    queryKey: ['filters'],
    queryFn: getFilters,
    staleTime: Infinity,
  })

  function handleSearchChange(e) {
    setSearch(e.target.value)
    setPage(1)
  }

  function handleFilterChange(setter) {
    return (value) => {
      setter(value)
      setPage(1)
    }
  }

  function openAdd() {
    setEditEmployee(null)
    setModalOpen(true)
  }

  function openEdit(emp) {
    setEditEmployee(emp)
    setModalOpen(true)
  }

  function openDelete(emp) {
    setDeleteEmployee(emp)
    setDeleteOpen(true)
  }

  const items = data?.items ?? []
  const total = data?.total ?? 0
  const totalPages = data?.total_pages ?? 0

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Employees</h1>
        <Button onClick={openAdd}>
          <Plus className="h-4 w-4 mr-2" /> Add Employee
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-4">
        <Input
          className="w-64"
          placeholder="Search by name…"
          value={search}
          onChange={handleSearchChange}
        />

        <Select value={country} onValueChange={handleFilterChange(setCountry)}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Country" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Countries</SelectItem>
            {filters?.countries?.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={department} onValueChange={handleFilterChange(setDepartment)}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Department" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Departments</SelectItem>
            {filters?.departments?.map((d) => <SelectItem key={d} value={d}>{d}</SelectItem>)}
          </SelectContent>
        </Select>

        <Select value={employmentType} onValueChange={handleFilterChange(setEmploymentType)}>
          <SelectTrigger className="w-44"><SelectValue placeholder="Type" /></SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            {['Full-time', 'Part-time', 'Contract', 'Intern'].map((t) => (
              <SelectItem key={t} value={t}>{t}</SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Table */}
      <div className="rounded-lg border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/50">
            <tr>
              {['Full Name', 'Job Title', 'Department', 'Country', 'Salary', 'Type', 'Hire Date', ''].map((h) => (
                <th key={h} className="px-4 py-3 text-left font-medium text-muted-foreground whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">Loading…</td></tr>
            )}
            {isError && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-destructive">Failed to load employees.</td></tr>
            )}
            {!isLoading && !isError && items.length === 0 && (
              <tr><td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">No employees found.</td></tr>
            )}
            {items.map((emp) => (
              <tr key={emp.id} className="border-t hover:bg-muted/20 transition-colors">
                <td className="px-4 py-3 font-medium whitespace-nowrap">{emp.full_name}</td>
                <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{emp.job_title}</td>
                <td className="px-4 py-3 whitespace-nowrap">{emp.department}</td>
                <td className="px-4 py-3 whitespace-nowrap">{emp.country}</td>
                <td className="px-4 py-3 whitespace-nowrap font-mono text-sm">
                  {formatSalary(emp.salary, emp.currency)}
                </td>
                <td className="px-4 py-3">
                  <Badge variant={EMP_TYPE_COLORS[emp.employment_type] ?? 'outline'}>
                    {emp.employment_type}
                  </Badge>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                  {emp.hire_date}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-1">
                    <Button variant="ghost" size="icon" onClick={() => openEdit(emp)}>
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button variant="ghost" size="icon" onClick={() => openDelete(emp)}>
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 0 && (
        <div className="flex items-center justify-between mt-4 text-sm text-muted-foreground">
          <span>
            Page {page} of {totalPages} &mdash; {total.toLocaleString()} total
          </span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
              Previous
            </Button>
            <Button variant="outline" size="sm" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
              Next
            </Button>
          </div>
        </div>
      )}

      <EmployeeModal
        open={modalOpen}
        onOpenChange={setModalOpen}
        employee={editEmployee}
      />

      {deleteEmployee && (
        <DeleteDialog
          open={deleteOpen}
          onOpenChange={setDeleteOpen}
          employee={deleteEmployee}
        />
      )}
    </div>
  )
}
