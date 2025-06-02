import React, { useState, useRef, useEffect } from 'react'

const ChatMessage = ({ type, content, isLoading = false }) => {
	return (
		<div className={`flex mb-4 ${type === 'user' ? 'justify-end' : 'justify-start'}`}>
			<div
				className={`
          max-w-[80%] p-3 rounded-lg 
          ${type === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}
          ${isLoading ? 'animate-pulse' : ''}
        `}
			>
				{isLoading ? (
					<div className="flex items-center">
						<span>Thinking</span>
						<div className="ml-2 flex space-x-1">
							<div className="w-2 h-2 bg-white rounded-full animate-bounce"></div>
							<div className="w-2 h-2 bg-white rounded-full animate-bounce delay-100"></div>
							<div className="w-2 h-2 bg-white rounded-full animate-bounce delay-200"></div>
						</div>
					</div>
				) : (
					<p className="whitespace-pre-wrap">{content}</p>
				)}
			</div>
		</div>
	)
}

const RepoChatbot = () => {
	const [repoUrl, setRepoUrl] = useState('')
	const [question, setQuestion] = useState('')
	const [messages, setMessages] = useState([])
	const [isLoading, setIsLoading] = useState(false)
	const [error, setError] = useState(null)
	const [isRepoQuestion, setIsRepoQuestion] = useState(false)
	const chatEndRef = useRef(null)

	const scrollToBottom = () => {
		chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
	}

	useEffect(() => {
		scrollToBottom()
	}, [messages])

	const handleSubmit = async (e) => {
		e.preventDefault()

		if (!question.trim()) return

		const userMessage = { type: 'user', content: question }
		setMessages((prev) => [...prev, userMessage])

		setError(null)
		setIsLoading(true)

		try {
			const payload = {
				question: question,
				repo_url: isRepoQuestion ? repoUrl : null
			}

			const response = await fetch('http://127.0.0.1:5000/chatbot', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(payload)
			})

			const data = await response.json()

			if (!response.ok) {
				throw new Error(data.error || 'Something went wrong')
			}

			const aiMessage = {
				type: 'ai',
				content: data.response,
				hasRepoContext: data.has_repo_context
			}
			setMessages((prev) => [...prev, aiMessage])
		} catch (err) {
			const errorMessage = { type: 'ai', content: `Error: ${err.message}` }
			setMessages((prev) => [...prev, errorMessage])
			console.error('Chatbot request error:', err)
		} finally {
			setIsLoading(false)
			setQuestion('')
		}
	}

	return (
		<div className="max-w-6xl mt-10 mx-auto p-4 bg-white shadow-lg rounded-xl">
			<div className="flex flex-col h-[700px]">
				<div className="bg-gray-100 rounded-t-xl p-4 border-b">
					<h2 className="text-2xl font-bold text-gray-800">🤖 Ask AI for explanations</h2>
					<div className="flex items-center mt-2">
						<label htmlFor="repo-toggle" className="mr-2 text-sm font-medium text-gray-700">
							Repository-Specific Question
						</label>
						<input
							type="checkbox"
							id="repo-toggle"
							checked={isRepoQuestion}
							onChange={() => setIsRepoQuestion(!isRepoQuestion)}
							className="form-checkbox h-4 w-4 text-blue-600"
						/>
					</div>
				</div>

				<div className="flex-grow overflow-y-auto p-4 space-y-3">
					{messages.map((msg, index) => (
						<ChatMessage
							key={index}
							type={msg.type}
							content={msg.content}
							isLoading={index === messages.length - 1 && isLoading}
						/>
					))}
					{isLoading && <ChatMessage type="ai" isLoading={true} />}
					<div ref={chatEndRef} />
				</div>

				<form onSubmit={handleSubmit} className="p-4 bg-gray-100 rounded-b-xl">
					{isRepoQuestion && (
						<div className="mb-2">
							<input
								type="text"
								value={repoUrl}
								onChange={(e) => setRepoUrl(e.target.value)}
								placeholder="GitHub Repository URL"
								disabled={isLoading}
								className="w-full px-3 py-2 border border-gray-300 rounded-md mb-2"
							/>
						</div>
					)}
					<div className="flex">
						<textarea
							value={question}
							onChange={(e) => setQuestion(e.target.value)}
							placeholder={
								isRepoQuestion
									? 'Ask a specific question about the repository'
									: 'Ask a general coding question'
							}
							disabled={isLoading}
							rows={2}
							className="flex-grow px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
							required
						/>
						<button
							type="submit"
							disabled={isLoading || (isRepoQuestion && !repoUrl)}
							className={`
                px-4 py-2 rounded-r-md text-white font-semibold 
                ${
					isLoading || (isRepoQuestion && !repoUrl)
						? 'bg-gray-400 cursor-not-allowed'
						: 'bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500'
				}
              `}
						>
							{isLoading ? 'Sending...' : 'Send'}
						</button>
					</div>
				</form>
			</div>
		</div>
	)
}

export default RepoChatbot
