import { FaGithub, FaSearch, FaSpinner } from 'react-icons/fa'

const RepositoryForm = ({ repoUrl, setRepoUrl, loading, handleSubmit, error }) => {
	return (
		<div className="bg-white shadow rounded-lg p-6 mb-6">
			<h2 className="text-lg font-medium text-gray-900 mb-4">Analyze GitHub Repository</h2>
			<form onSubmit={handleSubmit} className="flex flex-col sm:flex-row gap-4">
				<div className="flex-grow">
					<label htmlFor="repo-url" className="sr-only">
						GitHub Repository URL
					</label>
					<div className="relative rounded-md shadow-sm">
						<div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
							<FaGithub className="h-5 w-5 text-gray-400" />
						</div>
						<input
							type="text"
							id="repo-url"
							className="focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 py-3 pr-12 sm:text-sm border-gray-300 rounded-md"
							placeholder="Enter GitHub repository URL"
							value={repoUrl}
							onChange={(e) => setRepoUrl(e.target.value)}
							required
						/>
					</div>
				</div>
				<button
					type="submit"
					disabled={loading}
					className="inline-flex cursor-pointer items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
				>
					{loading ? (
						<>
							<FaSpinner className="animate-spin -ml-1 mr-2 h-5 w-5" />
							Analyzing...
						</>
					) : (
						<>
							<FaSearch className="-ml-1 mr-2 h-5 w-5" />
							Analyze
						</>
					)}
				</button>
			</form>
			{error && (
				<div className="mt-3 text-sm text-red-600">
					<p>{error}</p>
				</div>
			)}
		</div>
	)
}

export default RepositoryForm
