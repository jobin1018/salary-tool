import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'
import { getSummary, getCountryStats, getCountryJobTitles, getJobTitleStats } from '@/api/insights'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const COUNTRIES = [
  'India', 'USA', 'UK', 'UAE', 'Canada', 'Australia', 'Singapore', 'Germany', 'France', 'Netherlands',
]

const COUNTRY_CURRENCY = {
  India: 'INR', USA: 'USD', UK: 'GBP', UAE: 'AED',
  Canada: 'CAD', Australia: 'AUD', Singapore: 'SGD',
  Germany: 'EUR', France: 'EUR', Netherlands: 'EUR',
}

function StatCard({ title, value }) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-2xl font-bold">{value}</p>
      </CardContent>
    </Card>
  )
}

function fmt(n, currency = 'USD') {
  if (n == null) return '—'
  try {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency, maximumFractionDigits: 0 }).format(n)
  } catch {
    return Number(n).toLocaleString()
  }
}

function StatsRow({ stats, currency }) {
  if (!stats) return null
  return (
    <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-4">
      {[
        ['Count', stats.count?.toLocaleString()],
        ['Min', fmt(stats.min_salary, currency)],
        ['Max', fmt(stats.max_salary, currency)],
        ['Avg', fmt(stats.avg_salary, currency)],
        ['Median', fmt(stats.median_salary, currency)],
      ].map(([k, v]) => (
        <div key={k} className="rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">{k}</p>
          <p className="text-base font-semibold mt-1">{v}</p>
        </div>
      ))}
    </div>
  )
}

export default function InsightsPage() {
  const [selectedCountry, setSelectedCountry] = useState('')
  const [selectedJobTitle, setSelectedJobTitle] = useState('')

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['insights-summary'],
    queryFn: getSummary,
  })

  const { data: countryStats } = useQuery({
    queryKey: ['country-stats', selectedCountry],
    queryFn: () => getCountryStats(selectedCountry),
    enabled: Boolean(selectedCountry),
  })

  const { data: jobTitles } = useQuery({
    queryKey: ['job-titles', selectedCountry],
    queryFn: () => getCountryJobTitles(selectedCountry),
    enabled: Boolean(selectedCountry),
  })

  const { data: jobTitleStats } = useQuery({
    queryKey: ['job-title-stats', selectedCountry, selectedJobTitle],
    queryFn: () => getJobTitleStats(selectedCountry, selectedJobTitle),
    enabled: Boolean(selectedCountry) && Boolean(selectedJobTitle),
  })

  function handleCountryChange(country) {
    setSelectedCountry(country)
    setSelectedJobTitle('')
  }

  const deptData = Array.isArray(summary?.department_breakdown)
    ? summary.department_breakdown.map((d) => ({
        name: d.department,
        avg: Math.round(d.avg_salary ?? 0),
      }))
    : []

  const topEarners = summary?.top_earners ?? []
  const currency = selectedCountry ? COUNTRY_CURRENCY[selectedCountry] : 'USD'

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8">
      <h1 className="text-2xl font-bold">Insights</h1>

      {/* Summary Cards */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Global Summary</h2>
        {summaryLoading ? (
          <p className="text-muted-foreground">Loading…</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <StatCard title="Total Employees" value={summary?.total_employees?.toLocaleString() ?? '—'} />
            <StatCard title="Global Avg Salary" value={fmt(summary?.global_avg_salary)} />
            <StatCard title="Global Min Salary" value={fmt(summary?.global_min_salary)} />
            <StatCard title="Global Max Salary" value={fmt(summary?.global_max_salary)} />
          </div>
        )}
      </section>

      {/* Country Selector */}
      <section>
        <h2 className="text-lg font-semibold mb-3">Country Analysis</h2>
        <div className="flex flex-wrap gap-3">
          <Select value={selectedCountry} onValueChange={handleCountryChange}>
            <SelectTrigger className="w-48"><SelectValue placeholder="Select country" /></SelectTrigger>
            <SelectContent>
              {COUNTRIES.map((c) => <SelectItem key={c} value={c}>{c}</SelectItem>)}
            </SelectContent>
          </Select>

          {selectedCountry && jobTitles?.length > 0 && (
            <Select value={selectedJobTitle} onValueChange={setSelectedJobTitle}>
              <SelectTrigger className="w-56"><SelectValue placeholder="Select job title" /></SelectTrigger>
              <SelectContent>
                {jobTitles.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
              </SelectContent>
            </Select>
          )}
        </div>

        {selectedCountry && countryStats && (
          <Card className="mt-4">
            <CardHeader className="pb-0">
              <CardTitle className="text-base">{selectedCountry} — All Roles</CardTitle>
            </CardHeader>
            <CardContent>
              <StatsRow stats={countryStats} currency={currency} />
            </CardContent>
          </Card>
        )}

        {selectedJobTitle && jobTitleStats && (
          <Card className="mt-4">
            <CardHeader className="pb-0">
              <CardTitle className="text-base">{selectedCountry} — {selectedJobTitle}</CardTitle>
            </CardHeader>
            <CardContent>
              <StatsRow stats={jobTitleStats} currency={currency} />
            </CardContent>
          </Card>
        )}
      </section>

      {/* Avg Salary by Department Chart */}
      {deptData.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Avg Salary by Department</h2>
          <Card>
            <CardContent className="pt-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={deptData} margin={{ top: 0, right: 20, left: 20, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-35} textAnchor="end" tick={{ fontSize: 12 }} />
                  <YAxis tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v) => [`$${v.toLocaleString()}`, 'Avg Salary']} />
                  <Bar dataKey="avg" fill="hsl(222.2 47.4% 11.2%)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </section>
      )}

      {/* Top Earners */}
      {topEarners.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold mb-3">Top 10 Earners</h2>
          <div className="rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  {['Rank', 'Name', 'Job Title', 'Country', 'Salary'].map((h) => (
                    <th key={h} className="px-4 py-3 text-left font-medium text-muted-foreground">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {topEarners.map((emp, idx) => (
                  <tr key={emp.id} className="border-t hover:bg-muted/20 transition-colors">
                    <td className="px-4 py-3 font-mono text-muted-foreground">#{idx + 1}</td>
                    <td className="px-4 py-3 font-medium">{emp.full_name}</td>
                    <td className="px-4 py-3 text-muted-foreground">{emp.job_title}</td>
                    <td className="px-4 py-3">{emp.country}</td>
                    <td className="px-4 py-3 font-mono">
                      {fmt(emp.salary, emp.currency)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}
