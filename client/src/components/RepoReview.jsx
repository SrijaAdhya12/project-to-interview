import React, { useState } from 'react'
import { FaExclamationTriangle, FaCheckCircle, FaInfoCircle, FaTimesCircle } from 'react-icons/fa'
import LoadingState from './LoadingState'

const RepoReview = () => {
	const [repoUrl, setRepoUrl] = useState('')
	const [reviewData, setReviewData] = useState(null)
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState(null)

	const fetchCodeReview = async (e) => {
		e.preventDefault()

		const urlPattern = /^(https?:\/\/)?(www\.)?github\.com\/[a-zA-Z0-9-]+\/[a-zA-Z0-9-]+/
		if (!urlPattern.test(repoUrl)) {
			setError('Please enter a valid GitHub repository URL')
			return
		}

		try {
			setLoading(true)
			setError(null)

			const response = await fetch('https://project-to-interview.onrender.com/review', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ repo_url: repoUrl })
			})

			if (!response.ok) {
				throw new Error('Failed to fetch code review')
			}

			const data = await response.json()
			setReviewData(data)
			setLoading(false)
		} catch (err) {
			setError(err.message)
			setLoading(false)
		}
	}

	const getSeverityColor = (severity) => {
		switch (severity) {
			case 'High':
				return 'text-red-600'
			case 'Medium':
				return 'text-yellow-600'
			case 'Low':
				return 'text-blue-600'
			default:
				return 'text-gray-600'
		}
	}

	const getOverallQualityColor = (quality) => {
		switch (quality) {
			case 'Needs Improvement':
				return 'bg-red-100 text-red-800'
			case 'Average':
				return 'bg-yellow-100 text-yellow-800'
			case 'Good':
				return 'bg-green-100 text-green-800'
			default:
				return 'bg-gray-100 text-gray-800'
		}
	}

	const renderReviewResults = () => {
		if (loading) {
			return (
				<div className="flex justify-center items-center h-full min-h-[100px]">
					<div className="relative w-16 h-16">
						<div className="absolute inset-0 border-4 border-gray-200 rounded-full animate-ping"></div>
						<div className="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
					</div>
				</div>
			)
		}

		if (error) {
			return (
				<div className="bg-red-50 p-4 rounded-lg flex items-center">
					<FaTimesCircle className="mr-2 text-red-600" />
					<p className="text-red-800">{error}</p>
				</div>
			)
		}

		if (!reviewData) return null

		return (
			<div className="container mx-auto p-6 bg-gray-50 min-h-screen">
				<div className="max-w-4xl mx-auto">
					<h1 className="text-3xl font-bold mb-6 text-center">Code Review Results</h1>

					{/* Overall Code Quality */}
					<div
						className={`p-4 rounded-lg mb-6 text-center ${getOverallQualityColor(
							reviewData.overall_code_quality
						)}`}
					>
						<h2 className="text-xl font-semibold">
							Overall Code Quality: {reviewData.overall_code_quality}
						</h2>
					</div>

					{/* Code Smells Section */}
					<section className="mb-6">
						<h2 className="text-2xl font-semibold mb-4 flex items-center">
							<FaExclamationTriangle className="mr-2 text-yellow-600" /> Code Smells
						</h2>
						{reviewData.code_smells.length === 0 ? (
							<p className="text-green-600">No code smells detected!</p>
						) : (
							<div className="space-y-4">
								{reviewData.code_smells.map((smell, index) => (
									<div
										key={index}
										className={`p-4 rounded-lg border ${getSeverityColor(
											smell.severity
										)} bg-white shadow-md`}
									>
										<h3 className="font-bold mb-2">
											{smell.file} (Lines {smell.line_start}-{smell.line_end})
										</h3>
										<p className="mb-2">{smell.description}</p>
										<div className="flex items-center">
											<span className={`mr-2 font-semibold ${getSeverityColor(smell.severity)}`}>
												Severity: {smell.severity}
											</span>
											<p>{smell.suggestion}</p>
										</div>
									</div>
								))}
							</div>
						)}
					</section>

					{/* Architectural Suggestions */}
					<section className="mb-6">
						<h2 className="text-2xl font-semibold mb-4 flex items-center">
							<FaCheckCircle className="mr-2 text-green-600" /> Architectural Suggestions
						</h2>
						{reviewData.architectural_suggestions.length === 0 ? (
							<p className="text-green-600">No architectural suggestions found.</p>
						) : (
							<div className="space-y-4">
								{reviewData.architectural_suggestions.map((suggestion, index) => (
									<div key={index} className="p-4 rounded-lg bg-blue-50 border border-blue-200">
										<h3 className="font-bold mb-2">{suggestion.type}</h3>
										<p className="mb-2">{suggestion.description}</p>
										<p className="italic text-blue-700">
											Potential Impact: {suggestion.potential_impact}
										</p>
									</div>
								))}
							</div>
						)}
					</section>

					{/* Performance Recommendations */}
					<section className="mb-6">
						<h2 className="text-2xl font-semibold mb-4 flex items-center">
							<FaInfoCircle className="mr-2 text-blue-600" /> Performance Recommendations
						</h2>
						{reviewData.performance_recommendations.length === 0 ? (
							<p className="text-green-600">No performance recommendations found.</p>
						) : (
							<div className="space-y-4">
								{reviewData.performance_recommendations.map((recommendation, index) => (
									<div key={index} className="p-4 rounded-lg bg-purple-50 border border-purple-200">
										<h3 className="font-bold mb-2">{recommendation.file}</h3>
										<p className="mb-2">{recommendation.description}</p>
										<p className="italic text-purple-700">
											Suggested Optimization: {recommendation.suggested_optimization}
										</p>
									</div>
								))}
							</div>
						)}
					</section>

					{/* Best Practices Feedback */}
					<section>
						<h2 className="text-2xl font-semibold mb-4 flex items-center">
							<FaCheckCircle className="mr-2 text-green-600" /> Best Practices Feedback
						</h2>
						{reviewData.best_practices_feedback.length === 0 ? (
							<p className="text-green-600">No best practices feedback found.</p>
						) : (
							<div className="space-y-4">
								{reviewData.best_practices_feedback.map((feedback, index) => (
									<div key={index} className="p-4 rounded-lg bg-green-50 border border-green-200">
										<h3 className="font-bold mb-2">{feedback.category}</h3>
										<p>{feedback.description}</p>
									</div>
								))}
							</div>
						)}
					</section>
				</div>
			</div>
		)
	}

	return (
		<div className="min-h-screen bg-gray-100 p-6">
			<div className="max-w-2xl mx-auto bg-white shadow-md rounded-lg p-6">
				<form onSubmit={fetchCodeReview} className="mb-6">
					<div className="flex">
						<input
							type="text"
							value={repoUrl}
							onChange={(e) => setRepoUrl(e.target.value)}
							placeholder="Enter GitHub Repository URL (e.g., https://github.com/username/repo)"
							className="flex-grow p-3 border border-gray-300 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
						/>
						<button
							type="submit"
							disabled={loading}
							className="bg-blue-500 text-white px-6 py-3 rounded-r-lg hover:bg-blue-600 transition-colors disabled:opacity-50"
						>
							{loading ? 'Analyzing...' : 'Analyze'}
						</button>
					</div>
				</form>

				{renderReviewResults()}
			</div>
		</div>
	)
}

export default RepoReview
