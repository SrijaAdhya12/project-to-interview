import { FaSpinner, FaQuestionCircle } from 'react-icons/fa'

const LoadingState = ({ loading, questionsExist, error }) => {
	if (loading && !questionsExist) {
		return (
			<div className="text-center py-12">
				<FaSpinner className="mx-auto h-12 w-12 text-gray-400 animate-spin" />
				<h3 className="mt-2 text-sm font-medium text-gray-900">Analyzing repository...</h3>
				<p className="mt-1 text-sm text-gray-500">This may take a few moments.</p>
			</div>
		)
	}

	if (!loading && !questionsExist && !error) {
		return (
			<div className="text-center py-12">
				<FaQuestionCircle className="mx-auto h-12 w-12 text-gray-400" />
				<h3 className="mt-2 text-sm font-medium text-gray-900">No questions generated</h3>
				<p className="mt-1 text-sm text-gray-500">Enter a GitHub repository URL to get started.</p>
			</div>
		)
	}

	return null
}

export default LoadingState
