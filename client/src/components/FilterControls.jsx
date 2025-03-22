import { FaFilter } from 'react-icons/fa'

const FilterControls = ({ filters, setFilters, applyFilters, resetFilters, metadata }) => {
	return (
		<div className="bg-white shadow rounded-lg p-6 mb-6">
			<h2 className="text-lg font-medium text-gray-900 mb-4">Filter Questions</h2>
			<div className="flex flex-col sm:flex-row gap-4 mb-4">
				<div className="sm:w-1/3">
					<label htmlFor="difficulty" className="block text-sm font-medium text-gray-700 mb-1">
						Difficulty
					</label>
					<select
						id="difficulty"
						className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
						value={filters.difficulty}
						onChange={(e) => setFilters({ ...filters, difficulty: e.target.value })}
					>
						<option value="">All Difficulties</option>
						{metadata?.difficulty_levels.map((level) => (
							<option key={level} value={level}>
								{level}
							</option>
						))}
					</select>
				</div>
				<div className="sm:w-1/3">
					<label htmlFor="company" className="block text-sm font-medium text-gray-700 mb-1">
						Company Type
					</label>
					<select
						id="company"
						className="mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
						value={filters.company}
						onChange={(e) => setFilters({ ...filters, company: e.target.value })}
					>
						<option value="">All Companies</option>
						{metadata?.company_types.map((company) => (
							<option key={company} value={company}>
								{company}
							</option>
						))}
					</select>
				</div>
				<div className="sm:w-1/3 flex items-end space-x-2">
					<button
						type="button"
						onClick={applyFilters}
						className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
					>
						<FaFilter className="-ml-1 mr-2 h-4 w-4" />
						Apply Filters
					</button>
					<button
						type="button"
						onClick={resetFilters}
						className="flex-1 inline-flex justify-center items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md shadow-sm text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
					>
						Reset
					</button>
				</div>
			</div>
		</div>
	)
}

export default FilterControls
