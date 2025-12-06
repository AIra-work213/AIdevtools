import type { ComponentType, SVGProps } from 'react'

export interface Metric {
  title: string
  value: string
  change: string
  changeType: 'increase' | 'decrease'
  icon: ComponentType<SVGProps<SVGSVGElement>>
}

interface MetricsCardProps {
  metric: Metric
}

export function MetricsCard({ metric }: MetricsCardProps) {
  const { title, value, change, changeType, icon: Icon } = metric

  return (
    <div className="card">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Icon
            className={`h-6 w-6 ${
              changeType === 'increase' ? 'text-green-600' : 'text-red-600'
            }`}
            aria-hidden="true"
          />
        </div>
        <div className="ml-5 w-0 flex-1">
          <dl>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
              {title}
            </dt>
            <dd className="flex items-baseline">
              <div className="text-2xl font-semibold text-gray-900 dark:text-white">
                {value}
              </div>
              <div
                className={`ml-2 flex items-baseline text-sm font-semibold ${
                  changeType === 'increase'
                    ? 'text-green-600 dark:text-green-400'
                    : 'text-red-600 dark:text-red-400'
                }`}
              >
                {change}
              </div>
            </dd>
          </dl>
        </div>
      </div>
    </div>
  )
}