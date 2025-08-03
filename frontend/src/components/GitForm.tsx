import React, { useState } from 'react'
import { Plus, X } from 'lucide-react'

export default function GitForm({ onsubmit, isLoading, minUsers=2, maxUsers=5}: { onsubmit: (data: { users: string[] }) => void , isLoading: boolean, minUsers?: number, maxUsers?: number }) {
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
            setError(`Please enter between ${minUsers} and ${maxUsers} usernames`)
            return
        }
        setError('')
        onsubmit({users: trimmedUsers})
    }
    const getUserLabel = (index: number) => {
        if (index === 0) return "Your GitHub username"
        if (index === 1) return "Friend's GitHub username"
        return `Friend ${index}'s GitHub username`
      }

    return (
        <div className="max-w-md mx-auto rounded-lg border-2  bg-white/80 backdrop-blur-sm shadow-lg" style={{ padding: '2rem' }}>
          <div className="flex items-center justify-center" style={{ marginBottom: '2rem' }}>
            <h2 className="text-3xl font-bold text-black text-nowrap relative inline-block" style={{ padding: '0.5rem' }}>
              Let's find your compatibility
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
                            <span className="absolute inset-y-0  flex items-center text-gray-500" style={{ paddingLeft: '0.5rem', paddingTop: '1.25rem' }}>
                                github.com/
                            </span>
                        </div>
                        <input
                             id={`user-${index}`}
                             type="text"
                             value={user}
                             onChange={(e)=>updateUser(index, e.target.value)}
                             placeholder={`username`}
                             className="w-full p-3 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-black focus:border-black transition-all duration-200 bg-gray-50 focus:bg-white font-mono"
                             style={{ paddingLeft: '5.8rem', paddingTop: '0.45rem', paddingBottom: '0.5rem' }}
                        />
                     </div>
                    {users.length > minUsers && (
                        <button
                          type="button"
                          onClick={() => removeUser(index)}
                          className="p-3 text-red-500 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
                          style={{ marginBottom: '1rem' }}
                          title="Remove user"
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
            style={{ padding: '0.5rem', marginTop: '1rem' , marginBottom: '1rem' }}
            className="w-full border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-gray-400 hover:text-gray-700 transition-colors flex items-center justify-center gap-2 font-mono"
          >
            <Plus size={20} />
            Add another user ({users.length}/{maxUsers})
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
          style={{ padding: '0.5rem', marginTop: '1rem' , marginBottom: '1rem' }}
          className={`w-full rounded-lg font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 transform transition-all duration-200 font-mono ${
            isLoading 
              ? 'bg-gray-300 cursor-not-allowed text-gray-500' 
              : 'bg-black hover:bg-gray-800 text-white hover:shadow-lg active:scale-95'
          }`}
        >
          {isLoading ? 'GitM8ing...' : `GitM8 ${users.filter(u => u.trim()).length} Users`}
        </button>
      </div>
    </div>
  )
}