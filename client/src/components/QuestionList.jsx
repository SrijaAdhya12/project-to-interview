import QuestionCard from './QuestionCard'

const QuestionsList =({
	filteredQuestions,
	getDifficultyColor,
	getCompanyBadgeColor,
	feedbackStatus,
	submitFeedback,
	metadata
}) => {
	return (
		<div className="bg-white shadow rounded-lg overflow-hidden">
			<h2 className="text-lg font-medium text-gray-900 p-6 pb-0">
				Generated Questions ({filteredQuestions.length})
			</h2>
			<p className="text-sm text-gray-500 p-6 pt-2 pb-0">
				The following questions are generated based on the repository's content.
			</p>
			<ul className="divide-y divide-gray-200">
				{filteredQuestions.map((question, index) => (
					<li key={index} className="p-6">
						<QuestionCard
							question={question}
							index={index}
							difficultyColor={getDifficultyColor}
							companyBadgeColor={getCompanyBadgeColor}
							feedbackStatus={feedbackStatus[index]}
							onSubmitFeedback={submitFeedback}
							difficultyLevels={metadata?.difficulty_levels || []}
							companyTypes={metadata?.company_types || []}
						/>
					</li>
				))}
			</ul>
		</div>
	)
}

export default QuestionsList
