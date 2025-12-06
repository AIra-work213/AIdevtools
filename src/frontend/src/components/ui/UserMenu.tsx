import { Fragment, useState } from 'react'
import { Menu, Transition } from '@headlessui/react'
import {
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline'

export function UserMenu() {
  const [userName] = useState('QA Engineer')

  return (
    <Menu as="div" className="relative">
      <Menu.Button className="-m-1.5 flex items-center p-1.5">
        <span className="sr-only">Открыть меню пользователя</span>
        <UserCircleIcon className="h-8 w-8 rounded-full text-gray-400" aria-hidden="true" />
        <span className="hidden lg:flex lg:items-center">
          <span className="ml-4 text-sm font-semibold leading-6 text-gray-900 dark:text-gray-100">
            {userName}
          </span>
        </span>
      </Menu.Button>
      <Transition
        as={Fragment}
        enter="transition ease-out duration-100"
        enterFrom="transform opacity-0 scale-95"
        enterTo="transform opacity-100 scale-100"
        leave="transition ease-in duration-75"
        leaveFrom="transform opacity-100 scale-100"
        leaveTo="transform opacity-0 scale-95"
      >
        <Menu.Items className="absolute right-0 z-10 mt-2.5 w-32 origin-top-right rounded-md bg-white py-2 shadow-lg ring-1 ring-gray-900/5 focus:outline-none dark:bg-gray-800 dark:ring-gray-700">
          <Menu.Item>
            {({ active }) => (
              <button
                className={`${
                  active ? 'bg-gray-50 dark:bg-gray-700' : ''
                } flex w-full items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200`}
              >
                <UserCircleIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                Профиль
              </button>
            )}
          </Menu.Item>
          <Menu.Item>
            {({ active }) => (
              <button
                className={`${
                  active ? 'bg-gray-50 dark:bg-gray-700' : ''
                } flex w-full items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-200`}
              >
                <ArrowRightOnRectangleIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                Выйти
              </button>
            )}
          </Menu.Item>
        </Menu.Items>
      </Transition>
    </Menu>
  )
}