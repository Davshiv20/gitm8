import React, { useState } from 'react'
import { Plus, X } from 'lucide-react'
import { UI_TEXT, STYLING, CONFIG } from './constants'

export default function GitForm({ onsubmit, isLoading, minUsers=CONFIG.USER_LIMITS.MIN_USERS, maxUsers=CONFIG.USER_LIMITS.MAX_USERS}: { onsubmit: (data: { users: string[] }) => void , isLoading: boolean, minUsers?: number, maxUsers?: number }) {
    const [users, setUsers]= useState<string[]>(['',''])
    const [error, setError]= useState('')

    const addUser = () =>   {
        if(users.length < maxUsers){
            setUsers([...users, ''])
        }
    }

    const removeUser = (index: number) =>{
        if(users.length > minUsers){
            setUsers(users.filter((_, i) => i !== index))
        }
    }

    const updateUser = (index: number, value: string) =>{
        const newUsers = [...users]
        newUsers[index] = value
        setUsers(newUsers)
    }
    
    const handleSubmit = (e: React.FormEvent<HTMLFormElement>) =>{
        e.preventDefault()
        const trimmedUsers = users.map(user => user.trim()).filter(user => user !== '')
        if(trimmedUsers.length < minUsers || trimmedUsers.length > maxUsers){
            setError(UI_TEXT.ERROR_MESSAGES.USER_COUNT_RANGE.replace('{min}', minUsers.toString()).replace('{max}', maxUsers.toString()))
            return
        }
        setError('')
        onsubmit({users: trimmedUsers})
    }
    const getUserLabel = (index: number) => {
        if (index === 0) return UI_TEXT.USER_LABELS.YOUR_USERNAME
        if (index === 1) return UI_TEXT.USER_LABELS.FRIEND_USERNAME
        return UI_TEXT.USER_LABELS.FRIEND_NTH.replace('{n}', index.toString())
      }

    return (
        <div className="max-w-md mx-auto rounded-lg border-2  bg-white/80 backdrop-blur-sm shadow-lg" style={{ padding: STYLING.PADDING.FORM_CONTAINER }}>
          <div className="flex items-center justify-center" style={{ marginBottom: STYLING.MARGINS.FORM_HEADER }}>
            <h2 className="text-3xl font-bold text-black text-nowrap relative inline-block" style={{ padding: STYLING.SPACING.SMALL }}>
              {UI_TEXT.FORM_TITLE}
              <span className="absolute -bottom-1 left-0 w-full h-0.5 bg-black"></span>
            </h2>
            
          </div>
          
          <div className= "space-y-4">
            {users.map((user:string,index:number)=>(
                <div key={index} className="flex items-end gap-3">
                    <div className="flex-1">
                        <label htmlFor={`user-${index}`} className="block text-sm font-medium text-gray-700 font-mono tracking-tight" style={{ marginBottom: '0.5rem', marginTop: '0.5rem' }}>
                            {getUserLabel(index)}
                        </label>
                        <div className="relative">
                            <span className="absolute inset-y-0  flex items-center text-gray-500" style={{ paddingLeft: STYLING.SPACING.SMALL, paddingTop: '1.25rem' }}>
                                {UI_TEXT.GITHUB_PREFIX}
                            </span>
                        </div>
                        <input
                             id={`user-${index}`}
                             type="text"
                             value={user}
                             onChange={(e)=>updateUser(index, e.target.value)}
                             placeholder={UI_TEXT.USERNAME_PLACEHOLDER}
                             className="w-full p-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-black focus:border-black transition-all duration-200 bg-gray-50 focus:bg-white font-mono"
                             style={{ paddingLeft: STYLING.PADDING.INPUT_LEFT, paddingTop: STYLING.PADDING.INPUT_TOP, paddingBottom: STYLING.PADDING.INPUT_BOTTOM }}
                        />
                     </div>
                    {users.length > minUsers && (
                        <button
                          type="button"
                          onClick={() => removeUser(index)}
                          className="p-3 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                          style={{ marginBottom: STYLING.MARGINS.REMOVE_BUTTON }}
                          title={UI_TEXT.BUTTON_TEXT.REMOVE_USER}
                        >
                          <X size={20} />
                        </button>
                      )}
                    </div>
            ))}

          
{users.length < maxUsers && (
          <button
            type="button"
            onClick={addUser}
            style={{ padding: STYLING.SPACING.SMALL, marginTop: STYLING.MARGINS.ADD_BUTTON_TOP, marginBottom: STYLING.MARGINS.ADD_BUTTON_BOTTOM }}
            className="w-full border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-700 transition-colors flex items-center justify-center gap-2 font-mono"
          >
            <Plus size={20} />
            {UI_TEXT.BUTTON_TEXT.ADD_USER} ({users.length}/{maxUsers})
          </button>
        )}
        
        {error && (
          <div className="p-3 text-sm text-red-700 bg-red-50 border border-red-300 rounded-lg">
            {error}
          </div>
        )}
        
        <button
          onClick={(e) => {
            e.preventDefault()
            handleSubmit(e as any)
          }}
          disabled={isLoading}
          style={{ padding: STYLING.SPACING.SMALL, marginTop: STYLING.MARGINS.SUBMIT_BUTTON_TOP, marginBottom: STYLING.MARGINS.SUBMIT_BUTTON_BOTTOM }}
          className={`w-full rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transform transition-all duration-200 font-mono ${
            isLoading 
              ? 'bg-gray-300 cursor-not-allowed text-gray-500' 
              : 'bg-black hover:bg-gray-800 text-white hover:shadow-lg active:scale-95'
          }`}
        >
          {isLoading ? (
            <div className="flex items-center justify-center gap-2">
              <div className="loader"></div>

            </div>
          ) : (
            `${UI_TEXT.BUTTON_TEXT.SUBMIT} ${users.filter(u => u.trim()).length} Users`
          )}
        </button>
      </div>
    </div>
  )
}