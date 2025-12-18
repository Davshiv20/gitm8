import React, { useState } from 'react'
import { Form } from 'react-router'
import { Plus, X } from 'lucide-react'
import { UI_TEXT, STYLING, CONFIG } from './constants'
import type { UserCardType } from './types'


export default function GitForm({
  isLoading,
  minUsers = CONFIG.USER_LIMITS.MIN_USERS,
  maxUsers = CONFIG.USER_LIMITS.MAX_USERS,
}: {
  isLoading: boolean
  minUsers?: number
  maxUsers?: number
}) {
  const [users, setUsers] = useState<UserCardType[]>([])
  const [newUsername, setNewUsername] = useState('')
  const [error, setError] = useState('')

  // Fetch user data from GitHub
  const fetchUser = async (username: string) => {
    try {
      const response = await fetch(`https://api.github.com/users/${username}`)
      if (!response.ok) {
        throw new Error('User not found')
      }
      const data = await response.json()
      return {
        username: data.login,
        avatarUrl: data.avatar_url,
      }
    } catch (err) {
      console.error('Failed to fetch user:', err)
      return null
    }
  }

  const handleAddUser = async () => {
    setError('')
    const trimmedUsername = newUsername.trim()
    if (!trimmedUsername) return

    if (
      users.some(
        (user) => user.username.toLowerCase() === trimmedUsername.toLowerCase()
      )
    ) {
      setError(
        UI_TEXT.ERROR_MESSAGES.USERNAME_EXISTS ||
          'This user has already been added.'
      )
      return
    }

    if (users.length >= maxUsers) return

    // Show loading state for add button
    setError('')
    const userData = await fetchUser(trimmedUsername)
    if (userData) {
      setUsers([...users, userData])
      setNewUsername('')
    } else {
      setError(
        UI_TEXT.ERROR_MESSAGES.FETCH_FAIL ||
          'Failed to fetch GitHub user. Please check the username.'
      )
    }
  }

  const handleRemoveUser = (username: string) => {
    if (users.length > minUsers) {
      setUsers(users.filter((user) => user.username !== username))
    }
  }

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    if (users.length < minUsers || users.length > maxUsers) {
      e.preventDefault()
      setError(
        UI_TEXT.ERROR_MESSAGES.USER_COUNT_RANGE.replace(
          '{min}',
          minUsers.toString()
        ).replace('{max}', maxUsers.toString())
      )
      return
    }
    setError('')
  }

 
  const UserCard = ({
    user,
    onRemove,
  }: {
    user: UserCardType
    onRemove: (username: string) => void
  }) => (
    <div className="flex items-center justify-between border-2 border-gray-200 rounded-full bg-white/60 backdrop-blur-sm shadow-md transition-all duration-300 transform hover:scale-105" style={{padding : "0.5rem"}}>
      <div className="flex items-center" style={{gap:"0.5rem"}}>
        <img
          src={user.avatarUrl}
          alt={`${user.username}'s GitHub avatar`}
          className="w-8 h-8 rounded-full border border-gray-300"
        />
        <span className="text-sm font-medium text-gray-800 font-mono">
          {user.username}
        </span>
      </div>

        <button
          type="button"
          onClick={() => onRemove(user.username)}
          className=" rounded-full text-gray-500 hover:text-red-700 hover:bg-red-50 transition-colors"
          style={{padding: "0.25rem"}}
          title={UI_TEXT.BUTTON_TEXT.REMOVE_USER}
        >
          <X size={16} />
        </button>
    </div>
  )

  return (
    <div className="flex items-center justify-center min-h-[unset] bg-transparent p-0 font-sans antialiased">
      <div
        className="max-w-md mx-auto border-b-0.5 border-gray-200 rounded-xl backdrop-blur-xl bg-transparent shadow-[0px_10px_20px_0_rgba(0,0,0,0.5)]"
        style={{ padding: STYLING.PADDING.FORM_CONTAINER }}
      >
        <div
          className="flex flex-col items-center justify-center"
          style={{ marginBottom: STYLING.MARGINS.FORM_HEADER }}
        >
          <h2 className="text-3xl font-bold text-gray-900 text-center relative inline-block">
            {UI_TEXT.FORM_TITLE}
          </h2>
        </div>

        <Form method="post" onSubmit={handleSubmit}>
          <div className="flex flex-col gap-4">
            {users.length > 0 && (
              <div className="flex flex-wrap justify-center gap-4" style={{marginBottom: "12px", paddingLeft: "0.5rem", paddingRight: "0.5rem"}}>
                {users.map((user) => (
                  <UserCard
                    key={user.username}
                    user={user}
                    onRemove={handleRemoveUser}
                  />
                ))}
              </div>
            )}

            {users.length < maxUsers && (
              <div className="relative flex items-center">
                <span className="absolute left-3 text-sm text-gray-500 font-mono">
                  {UI_TEXT.GITHUB_PREFIX}
                </span>
                <input
                  type="text"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  placeholder={UI_TEXT.USERNAME_PLACEHOLDER}
                  className="w-full p-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-black focus:border-black transition-all duration-200 bg-gray-50 focus:bg-white font-mono"
                  style={{ paddingLeft: STYLING.PADDING.INPUT_LEFT, paddingTop: STYLING.PADDING.INPUT_TOP, paddingBottom: STYLING.PADDING.INPUT_BOTTOM }}
                  disabled={isLoading}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      handleAddUser()
                    }
                  }}
                />
                <button
                  type="button"
                  onClick={handleAddUser}
                  disabled={isLoading}
                  className={`absolute right-3 p-1 text-gray-500 hover:text-gray-700 transition-colors rounded-lg ${newUsername 
      ? "text-gray-700 bg-gray-300" 
      : "text-gray-500 hover:text-gray-700 hover:bg-gray-300"
                  }`}
                  title={UI_TEXT.BUTTON_TEXT.ADD_USER}
                >
                  <Plus size={20} className='hover:text-gray-700' />
                </button>
              </div>
            )}
          </div>

          {error && (
            <div className="text-sm text-red-700 bg-red-50 border border-red-300 rounded-lg" style={{padding: "0.5rem", marginTop: "1rem"}}>
              {error}
            </div>
          )}

          <input
            type="hidden"
            name="usernames"
            value={users.map(u => u.username).join(',')}
          />

          <div className="mt-6">
            <button
              type="submit"
              disabled={isLoading || users.length < minUsers}
              
              className={`w-full rounded-lg font-medium p-3 focus:outline-none focus:ring-2 focus:ring-offset-2 transform transition-all duration-200 font-mono ${
                isLoading || users.length < minUsers
                  ? 'bg-gray-300 cursor-not-allowed text-gray-500'
                  : 'bg-black hover:bg-gray-800 text-white hover:shadow-lg active:scale-95'
              }`}
              style={{
                padding: STYLING.SPACING.SMALL,
                marginTop: STYLING.MARGINS.SUBMIT_BUTTON_TOP,
                marginBottom: STYLING.MARGINS.SUBMIT_BUTTON_BOTTOM,
              }}
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 rounded-full border-2 border-gray-200 border-t-black animate-spin"></div>
                </div>
              ) : (
                `${UI_TEXT.BUTTON_TEXT.SUBMIT} ${users.length} Users`
              )}
            </button>
          </div>
        </Form>
      </div>
    </div>
  )
}