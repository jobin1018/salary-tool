import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createEmployee, updateEmployee } from '@/api/employees'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const CURRENCIES = ['USD', 'EUR', 'GBP', 'INR', 'AED', 'AUD', 'CAD', 'SGD']
const EMP_TYPES = ['Full-time', 'Part-time', 'Contract', 'Intern']

const EMPTY = {
  full_name: '',
  email: '',
  job_title: '',
  department: '',
  country: '',
  salary: '',
  currency: '',
  employment_type: '',
  hire_date: '',
}

function validate(form) {
  const errors = {}
  if (!form.full_name.trim()) errors.full_name = 'Required'
  if (!form.email.trim()) errors.email = 'Required'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errors.email = 'Invalid email'
  if (!form.job_title.trim()) errors.job_title = 'Required'
  if (!form.department.trim()) errors.department = 'Required'
  if (!form.country.trim()) errors.country = 'Required'
  if (!form.salary) errors.salary = 'Required'
  else if (isNaN(Number(form.salary)) || Number(form.salary) < 0) errors.salary = 'Must be >= 0'
  if (!form.currency) errors.currency = 'Required'
  if (!form.employment_type) errors.employment_type = 'Required'
  if (!form.hire_date) errors.hire_date = 'Required'
  else if (!/^\d{4}-\d{2}-\d{2}$/.test(form.hire_date)) errors.hire_date = 'Format: YYYY-MM-DD'
  return errors
}

export default function EmployeeModal({ open, onOpenChange, employee }) {
  const isEdit = Boolean(employee)
  const queryClient = useQueryClient()
  const [form, setForm] = useState(EMPTY)
  const [errors, setErrors] = useState({})
  const [serverError, setServerError] = useState('')

  useEffect(() => {
    if (open) {
      setErrors({})
      setServerError('')
      if (employee) {
        setForm({
          full_name: employee.full_name,
          email: employee.email,
          job_title: employee.job_title,
          department: employee.department,
          country: employee.country,
          salary: String(employee.salary),
          currency: employee.currency,
          employment_type: employee.employment_type,
          hire_date: employee.hire_date,
        })
      } else {
        setForm(EMPTY)
      }
    }
  }, [open, employee])

  const mutation = useMutation({
    mutationFn: (payload) =>
      isEdit ? updateEmployee(employee.id, payload) : createEmployee(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] })
      onOpenChange(false)
    },
    onError: (err) => {
      const msg = err?.response?.data?.detail || 'Something went wrong.'
      setServerError(typeof msg === 'string' ? msg : JSON.stringify(msg))
    },
  })

  function handleChange(e) {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    setErrors((prev) => ({ ...prev, [name]: undefined }))
  }

  function handleSelect(name, value) {
    setForm((prev) => ({ ...prev, [name]: value }))
    setErrors((prev) => ({ ...prev, [name]: undefined }))
  }

  function handleSubmit(e) {
    e.preventDefault()
    const errs = validate(form)
    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }
    const payload = { ...form, salary: Number(form.salary) }
    mutation.mutate(payload)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? 'Edit Employee' : 'Add Employee'}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          {serverError && (
            <p className="text-sm text-destructive">{serverError}</p>
          )}

          <Field label="Full Name" error={errors.full_name}>
            <Input name="full_name" value={form.full_name} onChange={handleChange} placeholder="Jane Smith" />
          </Field>

          <Field label="Email" error={errors.email}>
            <Input name="email" value={form.email} onChange={handleChange} placeholder="jane@company.com" />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Job Title" error={errors.job_title}>
              <Input name="job_title" value={form.job_title} onChange={handleChange} placeholder="Software Engineer" />
            </Field>
            <Field label="Department" error={errors.department}>
              <Input name="department" value={form.department} onChange={handleChange} placeholder="Engineering" />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Country" error={errors.country}>
              <Input name="country" value={form.country} onChange={handleChange} placeholder="USA" />
            </Field>
            <Field label="Hire Date" error={errors.hire_date}>
              <Input name="hire_date" value={form.hire_date} onChange={handleChange} placeholder="2024-01-15" />
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Salary" error={errors.salary}>
              <Input name="salary" value={form.salary} onChange={handleChange} placeholder="75000" type="number" min="0" />
            </Field>
            <Field label="Currency" error={errors.currency}>
              <Select value={form.currency} onValueChange={(v) => handleSelect('currency', v)}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  {CURRENCIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
                </SelectContent>
              </Select>
            </Field>
          </div>

          <Field label="Employment Type" error={errors.employment_type}>
            <Select value={form.employment_type} onValueChange={(v) => handleSelect('employment_type', v)}>
              <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
              <SelectContent>
                {EMP_TYPES.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
              </SelectContent>
            </Select>
          </Field>

          <DialogFooter className="pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving…' : isEdit ? 'Save Changes' : 'Add Employee'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function Field({ label, error, children }) {
  return (
    <div className="space-y-1">
      <Label>{label}</Label>
      {children}
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  )
}
