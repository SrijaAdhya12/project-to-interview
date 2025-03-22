export const getDifficultyColor = (difficulty) => {
	switch (difficulty) {
		case 'Easy':
			return 'bg-green-100 text-green-800'
		case 'Medium':
			return 'bg-yellow-100 text-yellow-800'
		case 'Hard':
			return 'bg-red-100 text-red-800'
		default:
			return 'bg-gray-100 text-gray-800'
	}
}

export const getCompanyBadgeColor = (company) => {
	switch (company) {
		case 'FAANG':
			return 'bg-blue-100 text-blue-800'
		case 'FinTech':
			return 'bg-purple-100 text-purple-800'
		case 'Enterprise':
			return 'bg-indigo-100 text-indigo-800'
		case 'Startups':
			return 'bg-green-100 text-green-800'
		case 'Healthcare':
			return 'bg-teal-100 text-teal-800'
		case 'Retail':
			return 'bg-orange-100 text-orange-800'
		default:
			return 'bg-gray-100 text-gray-800'
	}
}
