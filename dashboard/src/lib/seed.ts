import { supabase, PRODUCT_ID } from '@/lib/supabase'

// Sample claims seeded for brand-new accounts so the dashboard is never
// empty on first login. Only inserted when the user has zero records for
// this product. Dates are relative to "now" so the demo always looks live.
// All seeded rows carry is_demo = true so the UI can clearly label them
// as sample data.
export async function seedSampleClaims(userId: string): Promise<void> {
  const { count, error: countError } = await supabase
    .from('records')
    .select('id', { count: 'exact', head: true })
    .eq('product_id', PRODUCT_ID)
    .eq('customer_id', userId)

  if (countError) throw countError
  if (count && count > 0) return

  const days = (n: number) => new Date(Date.now() + n * 86400000).toISOString()

  type Sample = {
    title: string
    status: string
    priority: string
    due_date: string | null
    created_at: string
    details: Record<string, unknown>
  }

  const samples: Sample[] = [
    {
      title: 'Sarah Mitchell',
      status: 'Valid',
      priority: 'medium',
      due_date: days(45),
      created_at: days(-7),
      details: {
        claim_number: 'WC-2025-00412',
        order_id: 'ORD-77102',
        customer_name: 'Sarah Mitchell',
        amount: 249.99,
        product: 'Laptop power supply',
        description: 'Warranty claim for faulty power adapter',
      },
    },
    {
      title: 'James Rodriguez',
      status: 'Missing',
      priority: 'high',
      due_date: days(12),
      created_at: days(-6),
      details: {
        claim_number: 'WC-2025-00413',
        order_id: 'ORD-77103',
        customer_name: 'James Rodriguez',
        amount: 89.5,
        product: 'Mechanical keyboard',
        description: 'Missing proof of purchase',
      },
    },
    {
      title: 'Emily Zhang',
      status: 'Expired',
      priority: 'high',
      due_date: days(-20),
      created_at: days(-5),
      details: {
        claim_number: 'WC-2025-00414',
        order_id: 'ORD-77104',
        customer_name: 'Emily Zhang',
        amount: 320.0,
        product: 'Monitor',
        description: 'Screen replacement request past warranty window',
      },
    },
    {
      title: "Michael O'Connor",
      status: 'Flagged',
      priority: 'high',
      due_date: days(30),
      created_at: days(-4),
      details: {
        claim_number: 'WC-2025-00415',
        order_id: 'ORD-77105',
        customer_name: "Michael O'Connor",
        amount: 410.75,
        product: 'Graphics card',
        description: 'Duplicate documentation flagged for review',
      },
    },
    {
      title: 'Priya Sharma',
      status: 'Awaiting_Customer',
      priority: 'medium',
      due_date: days(60),
      created_at: days(-3),
      details: {
        claim_number: 'WC-2025-00416',
        order_id: 'ORD-77106',
        customer_name: 'Priya Sharma',
        amount: 64.0,
        product: 'Webcam',
        description: 'Waiting on customer serial number',
      },
    },
    {
      title: 'Daniel Kim',
      status: 'Valid',
      priority: 'low',
      due_date: days(90),
      created_at: days(-3),
      details: {
        claim_number: 'WC-2025-00417',
        order_id: 'ORD-77107',
        customer_name: 'Daniel Kim',
        amount: 540.0,
        product: 'Motherboard',
        description: 'Battery recall replacement claim',
      },
    },
    {
      title: 'Laura Novak',
      status: 'Duplicate',
      priority: 'medium',
      due_date: days(5),
      created_at: days(-1),
      details: {
        claim_number: 'WC-2025-00418',
        order_id: 'ORD-77108',
        customer_name: 'Laura Novak',
        amount: 120.4,
        product: 'Docking station',
        description: 'Duplicate of WC-2025-00412',
      },
    },
    {
      title: 'Tom Becker',
      status: 'Unreadable',
      priority: 'medium',
      due_date: null,
      created_at: days(0),
      details: {
        claim_number: 'WC-2025-00419',
        order_id: 'ORD-77109',
        customer_name: 'Tom Becker',
        amount: null,
        product: 'Headset',
        description: 'Scanned document could not be read',
      },
    },
  ]

  const payload = samples.map((s) => ({
    product_id: PRODUCT_ID,
    customer_id: userId,
    title: s.title,
    status: s.status,
    label: null,
    priority: s.priority,
    details: s.details,
    due_date: s.due_date,
    created_at: s.created_at,
    is_demo: true,
  }))

  const { error } = await supabase.from('records').insert(payload)
  if (error) throw error
}
