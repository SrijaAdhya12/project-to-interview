import { useState } from 'react'
import { FaCheck, FaTimes } from 'react-icons/fa'
import { BsBarChartFill, BsBuilding, BsBriefcase } from 'react-icons/bs'

const QuestionCard = ({
	question,
	index,
	difficultyColor,
	companyBadgeColor,
	feedbackStatus,
	onSubmitFeedback,
	difficultyLevels,
	companyTypes
}) => {
	const [isEditingFeedback, setIsEditingFeedback] = useState(false)
	const [difficultyFeedback, setDifficultyFeedback] = useState(question.difficulty)
	const [companiesFeedback, setCompaniesFeedback] = useState([...question.companies])

	const handleCompanyToggle = (company) => {
		if (companiesFeedback.includes(company)) {
			setCompaniesFeedback(companiesFeedback.filter((c) => c !== company))
		} else {
			setCompaniesFeedback([...companiesFeedback, company])
		}
	}

	const handleSubmitFeedback = () => {
		onSubmitFeedback(index, difficultyFeedback, companiesFeedback)
		setIsEditingFeedback(false)
	}

	return (
		<div className="space-y-3">
			<div className="flex items-start justify-between">
				<h3 className="text-lg font-medium text-gray-900">{question.question}</h3>
				<div
					className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${difficultyColor(
						question.difficulty
					)}`}
				>
					<BsBarChartFill className="mr-1" />
					{question.difficulty}
				</div>
			</div>

			{question.context && <p className="text-sm text-gray-500">{question.context}</p>}

			<div className="flex flex-wrap gap-2 mt-2">
				{question.companies.map((company) => (
					<span
						key={company}
						className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${companyBadgeColor(
							company
						)}`}
					>
						<BsBuilding className="mr-1" />
						{company}
					</span>
				))}
			</div>

			<div className="pt-2">
				{feedbackStatus === 'success' && (
					<div className="flex items-center text-sm text-green-600">
						<FaCheck className="mr-1" />
						Feedback submitted successfully!
					</div>
				)}

				{feedbackStatus === 'error' && (
					<div className="flex items-center text-sm text-red-600">
						<FaTimes className="mr-1" />
						Failed to submit feedback.
					</div>
				)}

				{!feedbackStatus && !isEditingFeedback && (
					<button
						onClick={() => setIsEditingFeedback(true)}
						className="text-sm text-blue-600 hover:text-blue-800"
					>
						Provide feedback on this classification
					</button>
				)}

				{isEditingFeedback && (
					<div className="bg-gray-50 p-4 rounded-md mt-2 space-y-4">
						<h4 className="font-medium text-gray-900">Edit Classification</h4>

						<div>
							<label className="block text-sm font-medium text-gray-700 mb-1">Difficulty</label>
							<select
								className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
								value={difficultyFeedback}
								onChange={(e) => setDifficultyFeedback(e.target.value)}
							>
								{difficultyLevels.map((level) => (
									<option key={level} value={level}>
										{level}
									</option>
								))}
							</select>
						</div>

						<div>
							<label className="block text-sm font-medium text-gray-700 mb-1">Companies</label>
							<div className="flex flex-wrap gap-2">
								{companyTypes.map((company) => (
									<button
										key={company}
										type="button"
										onClick={() => handleCompanyToggle(company)}
										className={`inline-flex items-center px-2.5 py-1.5 border rounded-full text-xs font-medium ${
											companiesFeedback.includes(company)
												? `${companyBadgeColor(company)} border-transparent`
												: 'border-gray-300 text-gray-700 bg-white'
										}`}
									>
										<BsBriefcase className="mr-1" />
										{company}
									</button>
								))}
							</div>
						</div>

						<div className="flex justify-end space-x-2">
							<button
								type="button"
								onClick={() => setIsEditingFeedback(false)}
								className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
							>
								Cancel
							</button>
							<button
								type="button"
								onClick={handleSubmitFeedback}
								className="inline-flex items-center px-3 py-1.5 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
							>
								Submit Feedback
							</button>
						</div>
					</div>
				)}
			</div>
		</div>
	)
}

export default QuestionCard
