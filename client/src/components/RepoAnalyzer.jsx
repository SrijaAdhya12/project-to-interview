import { useState } from 'react'
import { Header, RepositoryForm, FilterControls, QuestionsList, LoadingState } from './index'
import { getDifficultyColor, getCompanyBadgeColor } from '../utils/ColorUtils'

const RepoAnalyzer = () => {
	const [repoUrl, setRepoUrl] = useState('')
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState('')
	const [questions, setQuestions] = useState([])
	const [filteredQuestions, setFilteredQuestions] = useState([])
	const [filters, setFilters] = useState({
		difficulty: '',
		company: ''
	})
	const [metadata, setMetadata] = useState(null)
	const [feedbackStatus, setFeedbackStatus] = useState({})

	const handleSubmit = async (e) => {
		e.preventDefault()

		if (!repoUrl.includes('github.com')) {
			setError('Please enter a valid GitHub repository URL')
			return
		}

		setLoading(true)
		setError('')
		setQuestions([])
		setFilteredQuestions([])
		setMetadata(null)

		try {
			const response = await fetch('http://127.0.0.1:5000/analyze', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ repo_url: repoUrl })
			})

			const data = await response.json()

			if (!response.ok) {
				throw new Error(data.error || 'Failed to analyze repository')
			}

			if (data.structured) {
				setQuestions(data.questions)
				setFilteredQuestions(data.questions)
				setMetadata(data.metadata)
			} else {
				setError('Received unstructured response from the server')
			}
		} catch (err) {
			setError(err.message)
		} finally {
			setLoading(false)
		}
	}

	const applyFilters = async () => {
		if (filters.difficulty === '' && filters.company === '') {
			setFilteredQuestions(questions)
			return
		}

		try {
			const response = await fetch('http://127.0.0.1:5000/filter', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					questions: questions,
					difficulty: filters.difficulty || undefined,
					company: filters.company || undefined
				})
			})

			const data = await response.json()

			if (!response.ok) {
				throw new Error(data.error || 'Failed to filter questions')
			}

			setFilteredQuestions(data.questions)
		} catch (err) {
			setError(err.message)
		}
	}

	const resetFilters = () => {
		setFilters({
			difficulty: '',
			company: ''
		})
		setFilteredQuestions(questions)
	}

	const submitFeedback = async (questionIndex, difficultyFeedback, companiesFeedback) => {
		const question = filteredQuestions[questionIndex]

		try {
			const response = await fetch('http://127.0.0.1:5000/feedback', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					question_id: questionIndex,
					question: question.question,
					context: question.context || '',
					correct_difficulty: difficultyFeedback,
					correct_companies: companiesFeedback
				})
			})

			const data = await response.json()

			if (!response.ok) {
				throw new Error(data.error || 'Failed to submit feedback')
			}

			setFeedbackStatus({
				...feedbackStatus,
				[questionIndex]: 'success'
			})

			setTimeout(() => {
				setFeedbackStatus({
					...feedbackStatus,
					[questionIndex]: ''
				})
			}, 3000)
		} catch (err) {
			setFeedbackStatus({
				...feedbackStatus,
				[questionIndex]: 'error'
			})
			setError(err.message)
		}
	}

	return (
		<div className="min-h-screen bg-gray-50">

			<main className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
				<RepositoryForm
					repoUrl={repoUrl}
					setRepoUrl={setRepoUrl}
					loading={loading}
					handleSubmit={handleSubmit}
					error={error}
				/>

				{questions.length > 0 && (
					<FilterControls
						filters={filters}
						setFilters={setFilters}
						applyFilters={applyFilters}
						resetFilters={resetFilters}
						metadata={metadata}
					/>
				)}

				{filteredQuestions.length > 0 && (
					<QuestionsList
						filteredQuestions={filteredQuestions}
						getDifficultyColor={getDifficultyColor}
						getCompanyBadgeColor={getCompanyBadgeColor}
						feedbackStatus={feedbackStatus}
						submitFeedback={submitFeedback}
						metadata={metadata}
					/>
				)}

				<LoadingState loading={loading} questionsExist={questions.length > 0} error={error} />
			</main>
		</div>
	)
}

export default RepoAnalyzer
