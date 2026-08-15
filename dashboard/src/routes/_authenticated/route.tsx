import { createFileRoute, redirect } from '@tanstack/react-router'
import { syncAuthFromSession } from '@/stores/auth-store'
import { supabase, PRODUCT_ID } from '@/lib/supabase'
import { seedSampleClaims } from '@/lib/seed'
import { AuthenticatedLayout } from '@/components/layout/authenticated-layout'

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async () => {
    const { data } = await supabase.auth.getSession()
    if (!data.session) {
      throw redirect({ to: '/sign-up' })
    }
    await syncAuthFromSession()
    // Seed sample claims once per user so new accounts are never empty.
    const seedKey = `cp_seeded_${data.session.user.id}`
    if (!localStorage.getItem(seedKey)) {
      try {
        await seedSampleClaims(data.session.user.id)
        localStorage.setItem(seedKey, '1')
      } catch (e) {
        console.error('sample claim seeding failed', e)
      }
    }
    // Write audit log for session start (once per browser session)
    const auditKey = `audit_session_${data.session.user.id}`
    if (!sessionStorage.getItem(auditKey)) {
      sessionStorage.setItem(auditKey, '1')
      void supabase.from('audit_log').insert({
        product_id: PRODUCT_ID,
        customer_id: data.session.user.id,
        action: 'session.started',
        entity: 'auth',
        entity_id: data.session.user.id,
      })
    }
    // Fire welcome email once per user (magic link confirmation)
    const welcomeKey = `welcome_sent_${data.session.user.email}`
    if (!localStorage.getItem(welcomeKey)) {
      localStorage.setItem(welcomeKey, '1')
      fetch('https://web-production-6adc6.up.railway.app/send-welcome', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email: data.session.user.email,
          product_name: (import.meta.env.VITE_PRODUCT_NAME as string),
          dashboard_url: window.location.origin,
        }),
      }).catch(() => {})
    }
  },
  component: AuthenticatedLayout,
})
