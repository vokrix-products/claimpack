import { useEffect, useState } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Header } from '@/components/layout/header'
import { Main } from '@/components/layout/main'
import { ProfileDropdown } from '@/components/profile-dropdown'
import { Search } from '@/components/search'
import { ThemeSwitch } from '@/components/theme-switch'
import { JobsCard } from '@/features/jobs/components/jobs-card'
import { NotificationsBell } from '@/components/notifications-bell'
import { PRODUCT_ARCHETYPE, RECORDS_LABEL } from '@/product-config'
import { ReportCard } from './components/report-card'
import { Overview } from './components/overview'
import { RecentActivity } from './components/recent-activity'
import { UpcomingExpirations } from './components/upcoming-expirations'
import { useDashboardStats } from './data/dashboard'
import { supabase, PRODUCT_ID } from '@/lib/supabase'
import { Skeleton } from '@/components/ui/skeleton'
import { NumberTicker } from '@/components/magicui/number-ticker'

const recordsLower = RECORDS_LABEL.toLowerCase()

function Trend({ current, previous }: { current: number; previous: number }) {
  if (previous === 0 && current === 0) return null
  const diff = current - previous
  const pct = previous === 0 ? 100 : Math.round(Math.abs(diff / previous) * 100)
  if (diff === 0) return <span className='text-xs text-muted-foreground'>No change</span>
  return (
    <span className={diff > 0 ? 'text-xs text-success' : 'text-xs text-destructive'}>
      {diff > 0 ? '↑' : '↓'} {pct}% vs last week
    </span>
  )
}

export function Dashboard() {
  const { data, isLoading } = useDashboardStats()
  const [showUpgradeBanner, setShowUpgradeBanner] = useState(false)
  const [showDemoBanner, setShowDemoBanner] = useState(false)
  const [demoUserId, setDemoUserId] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('upgraded') === 'true') {
      window.history.replaceState({}, '', window.location.pathname)
      setTimeout(() => setShowUpgradeBanner(true), 0)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()
        if (!user || cancelled) return
        if (localStorage.getItem(`cp_demo_banner_dismissed_${user.id}`)) return
        const { count } = await supabase
          .from('records')
          .select('id', { count: 'exact', head: true })
          .eq('product_id', PRODUCT_ID)
          .eq('customer_id', user.id)
          .eq('is_demo', true)
        if (!cancelled && count && count > 0) {
          setDemoUserId(user.id)
          setShowDemoBanner(true)
        }
      } catch {}
    })()
    return () => {
      cancelled = true
    }
  }, [])

  function dismissDemoBanner() {
    setShowDemoBanner(false)
    if (demoUserId) {
      localStorage.setItem(`cp_demo_banner_dismissed_${demoUserId}`, '1')
    }
  }

  async function handleRefreshSession() {
    await supabase.auth.refreshSession()
    window.location.reload()
  }

  return (
    <>
      {/* ===== Top Heading ===== */}
      <Header>
        <Search />
        <ThemeSwitch />
        <NotificationsBell />
        <ProfileDropdown />
      </Header>

      {/* ===== Main ===== */}
      <Main>
        {showUpgradeBanner && (
          <div className='flex items-center justify-between rounded-lg border border-success bg-success/10 px-4 py-3 text-sm text-success mb-4'>
            <span>Payment successful! Refresh your session to activate full access.</span>
            <button
              onClick={handleRefreshSession}
              className='ml-4 font-medium underline underline-offset-2 hover:no-underline'
            >
              Refresh now
            </button>
          </div>
        )}
        {showDemoBanner && (
          <div className='mb-4 flex items-center justify-between gap-4 rounded-lg border border-warning bg-warning/10 px-4 py-3 text-sm text-warning'>
            <span>
              You're viewing <strong>sample claims</strong>. Upload your own files to
              replace them, or delete any sample with the trash icon.
            </span>
            <button
              onClick={dismissDemoBanner}
              className='shrink-0 font-medium underline underline-offset-2 hover:no-underline'
            >
              Dismiss
            </button>
          </div>
        )}
        <div className='mb-2 flex items-center justify-between space-y-2'>
          <h1 className='text-2xl font-bold tracking-tight'>{RECORDS_LABEL} Overview</h1>
        </div>
        <div className='space-y-4'>
          <JobsCard />
          {PRODUCT_ARCHETYPE === 'report' && <ReportCard />}
          <div className='grid gap-4 sm:grid-cols-3'>
            <Card>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>Total {RECORDS_LABEL}</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className='h-8 w-16' />
                ) : (
                  <>
                    <div className='text-2xl font-bold tracking-tight'>
                      <NumberTicker value={data?.total ?? 0} />
                    </div>
                    <Trend current={data?.total ?? 0} previous={data?.totalPrevWeek ?? 0} />
                  </>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>Needs Attention</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className='h-8 w-16' />
                ) : (
                  <>
                    <div className='text-2xl font-bold tracking-tight text-destructive'>
                      <NumberTicker value={data?.needsAttention ?? 0} />
                    </div>
                    <Trend current={data?.needsAttention ?? 0} previous={data?.needsAttentionPrevWeek ?? 0} />
                  </>
                )}
              </CardContent>
            </Card>
            <Card>
              <CardHeader className='flex flex-row items-center justify-between space-y-0 pb-2'>
                <CardTitle className='text-sm font-medium'>Added This Week</CardTitle>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <Skeleton className='h-8 w-16' />
                ) : (
                  <>
                    <div className='text-2xl font-bold tracking-tight'>
                      <NumberTicker value={data?.addedThisWeek ?? 0} />
                    </div>
                    <Trend current={data?.addedThisWeek ?? 0} previous={data?.addedPrevWeek ?? 0} />
                  </>
                )}
              </CardContent>
            </Card>
          </div>
          <div className='grid grid-cols-1 gap-4 lg:grid-cols-7'>
            <Card className='col-span-1 lg:col-span-4'>
              <CardHeader>
                <CardTitle>{RECORDS_LABEL} by Status</CardTitle>
              </CardHeader>
              <CardContent className='ps-2'>
                <Overview />
              </CardContent>
            </Card>
            <Card className='col-span-1 lg:col-span-3'>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
                <CardDescription>Latest uploaded {recordsLower} and updates</CardDescription>
              </CardHeader>
              <CardContent>
                <RecentActivity />
              </CardContent>
            </Card>
          </div>
          <Card>
            <CardHeader>
              <CardTitle>Upcoming Expirations</CardTitle>
              <CardDescription>{RECORDS_LABEL} expiring in the next 90 days</CardDescription>
            </CardHeader>
            <CardContent>
              <UpcomingExpirations />
            </CardContent>
          </Card>
        </div>
      </Main>
    </>
  )
}
