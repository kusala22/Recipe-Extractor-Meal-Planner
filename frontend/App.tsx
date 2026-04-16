import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import axios from 'axios'
import {
  API_BASE_URL,
  extractRecipe,
  getRecipeDetails,
  getSavedRecipes,
} from './services/api'
import './App.css'

type Ingredient = {
  quantity: string
  unit: string
  item: string
}

type NutritionEstimate = {
  calories?: number
  protein?: string
  carbs?: string
  fat?: string
}

type RecipeData = {
  title: string
  cuisine?: string
  prep_time?: string
  cook_time?: string
  total_time?: string
  servings?: string
  difficulty?: string
  ingredients: Ingredient[]
  instructions: string[]
  nutrition_estimate?: NutritionEstimate
  substitutions: string[]
  shopping_list: Record<string, string[]>
  related_recipes: string[]
}

type RecipeSummary = {
  id: number
  url: string
  title: string
  cuisine?: string
  difficulty?: string
  created_at: string
}

type RecipeDetail = {
  id: number
  url: string
  title: string
  data: RecipeData
  created_at: string
}

type ExtractResponse = {
  source: 'cache' | 'live'
  data: RecipeData
}

function App() {
  const [recipeUrl, setRecipeUrl] = useState('')
  const [recipes, setRecipes] = useState<RecipeSummary[]>([])
  const [selectedRecipeId, setSelectedRecipeId] = useState<number | null>(null)
  const [selectedRecipe, setSelectedRecipe] = useState<RecipeDetail | null>(null)
  const [latestResult, setLatestResult] = useState<ExtractResponse | null>(null)
  const [loadingList, setLoadingList] = useState(true)
  const [extracting, setExtracting] = useState(false)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void loadRecipes()
  }, [])

  useEffect(() => {
    if (selectedRecipeId === null) {
      setSelectedRecipe(null)
      return
    }

    void loadRecipeDetail(selectedRecipeId)
  }, [selectedRecipeId])

  const loadRecipes = async () => {
    try {
      setLoadingList(true)
      const savedRecipes = await getSavedRecipes()
      setRecipes(savedRecipes)

      if (savedRecipes.length > 0) {
        setSelectedRecipeId((currentId) => currentId ?? savedRecipes[0].id)
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load saved recipes right now.'))
    } finally {
      setLoadingList(false)
    }
  }

  const loadRecipeDetail = async (recipeId: number) => {
    try {
      setLoadingDetail(true)
      const detail = await getRecipeDetails(recipeId)
      setSelectedRecipe(detail)
    } catch (err) {
      setError(getErrorMessage(err, 'Unable to load this recipe.'))
    } finally {
      setLoadingDetail(false)
    }
  }

  const handleExtract = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()

    if (!recipeUrl.trim()) {
      setError('Paste a recipe URL before extracting.')
      return
    }

    try {
      setExtracting(true)
      setError(null)

      const result = await extractRecipe(recipeUrl.trim())
      setLatestResult(result)
      await loadRecipes()
      setRecipeUrl('')
    } catch (err) {
      setError(getErrorMessage(err, 'Recipe extraction failed.'))
    } finally {
      setExtracting(false)
    }
  }

  const activeRecipe = selectedRecipe?.data ?? latestResult?.data ?? null

  return (
    <main className="app-shell">
      <section className="hero-panel">
        <div className="hero-copy">
          <p className="eyebrow">Recipe Extractor & Meal Planner</p>
          <h1>Turn recipe links into clean, usable meal data.</h1>
          <p className="hero-text">
            Extract ingredients, instructions, substitutions, nutrition, and a
            grouped shopping list from recipe pages in one place.
          </p>
        </div>

        <form className="extract-form" onSubmit={handleExtract}>
          <label htmlFor="recipe-url">Recipe URL</label>
          <div className="extract-row">
            <input
              id="recipe-url"
              type="url"
              placeholder="https://example.com/my-favorite-recipe"
              value={recipeUrl}
              onChange={(event) => setRecipeUrl(event.target.value)}
            />
            <button type="submit" disabled={extracting}>
              {extracting ? 'Extracting...' : 'Extract Recipe'}
            </button>
          </div>
          <p className="hint">
            The backend scrapes the page, runs structured extraction, and saves
            the result to Postgres. Frontend API target:{' '}
            <code>{API_BASE_URL}</code>
          </p>
        </form>

        {error ? <div className="status error">{error}</div> : null}

        {latestResult ? (
          <div className="status success">
            Latest extraction came from <strong>{latestResult.source}</strong>.
          </div>
        ) : null}
      </section>

      <section className="workspace">
        <aside className="panel sidebar">
          <div className="panel-head">
            <div>
              <p className="panel-kicker">Saved Recipes</p>
              <h2>Library</h2>
            </div>
            <button
              type="button"
              className="ghost-button"
              onClick={() => void loadRecipes()}
              disabled={loadingList}
            >
              Refresh
            </button>
          </div>

          <div className="recipe-list">
            {loadingList ? (
              <p className="empty-state">Loading saved recipes...</p>
            ) : recipes.length === 0 ? (
              <p className="empty-state">
                No recipes saved yet. Extract one to populate the library.
              </p>
            ) : (
              recipes.map((recipe) => (
                <button
                  key={recipe.id}
                  type="button"
                  className={`recipe-card ${
                    selectedRecipeId === recipe.id ? 'active' : ''
                  }`}
                  onClick={() => setSelectedRecipeId(recipe.id)}
                >
                  <span className="recipe-title">
                    {recipe.title || 'Untitled recipe'}
                  </span>
                  <span className="recipe-meta">
                    {recipe.cuisine || 'Unknown cuisine'} •{' '}
                    {recipe.difficulty || 'medium'}
                  </span>
                  <span className="recipe-date">
                    {formatDate(recipe.created_at)}
                  </span>
                </button>
              ))
            )}
          </div>
        </aside>

        <section className="panel detail-panel">
          <div className="panel-head">
            <div>
              <p className="panel-kicker">Recipe Detail</p>
              <h2>
                {activeRecipe?.title ||
                  'Select a saved recipe or run a fresh extraction'}
              </h2>
            </div>
            {selectedRecipe ? (
              <a className="source-link" href={selectedRecipe.url} target="_blank">
                Open source
              </a>
            ) : null}
          </div>

          {loadingDetail ? (
            <p className="empty-state">Loading recipe details...</p>
          ) : activeRecipe ? (
            <div className="detail-grid">
              <section className="info-strip">
                <InfoCard label="Cuisine" value={activeRecipe.cuisine} />
                <InfoCard label="Difficulty" value={activeRecipe.difficulty} />
                <InfoCard label="Prep" value={activeRecipe.prep_time} />
                <InfoCard label="Cook" value={activeRecipe.cook_time} />
                <InfoCard label="Total" value={activeRecipe.total_time} />
                <InfoCard label="Servings" value={activeRecipe.servings} />
              </section>

              <section className="detail-columns">
                <div className="content-card">
                  <h3>Ingredients</h3>
                  <ul className="stack-list">
                    {activeRecipe.ingredients.map((ingredient, index) => (
                      <li key={`${ingredient.item}-${index}`}>
                        {[ingredient.quantity, ingredient.unit, ingredient.item]
                          .filter(Boolean)
                          .join(' ')}
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="content-card">
                  <h3>Instructions</h3>
                  <ol className="steps-list">
                    {activeRecipe.instructions.map((step, index) => (
                      <li key={`${index}-${step}`}>{step}</li>
                    ))}
                  </ol>
                </div>

                <div className="content-card">
                  <h3>Nutrition</h3>
                  <div className="nutrition-grid">
                    <InfoCard
                      label="Calories"
                      value={
                        activeRecipe.nutrition_estimate?.calories?.toString() ||
                        '0'
                      }
                    />
                    <InfoCard
                      label="Protein"
                      value={activeRecipe.nutrition_estimate?.protein}
                    />
                    <InfoCard
                      label="Carbs"
                      value={activeRecipe.nutrition_estimate?.carbs}
                    />
                    <InfoCard
                      label="Fat"
                      value={activeRecipe.nutrition_estimate?.fat}
                    />
                  </div>
                </div>

                <div className="content-card">
                  <h3>Substitutions</h3>
                  <ul className="stack-list">
                    {activeRecipe.substitutions.length > 0 ? (
                      activeRecipe.substitutions.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))
                    ) : (
                      <li>No substitutions provided.</li>
                    )}
                  </ul>
                </div>

                <div className="content-card">
                  <h3>Shopping List</h3>
                  {Object.keys(activeRecipe.shopping_list).length > 0 ? (
                    <div className="shopping-groups">
                      {Object.entries(activeRecipe.shopping_list).map(
                        ([group, items]) => (
                          <div key={group} className="shopping-group">
                            <h4>{group}</h4>
                            <ul className="stack-list">
                              {items.map((item, index) => (
                                <li key={`${item}-${index}`}>{item}</li>
                              ))}
                            </ul>
                          </div>
                        ),
                      )}
                    </div>
                  ) : (
                    <p className="empty-inline">No shopping list generated.</p>
                  )}
                </div>

                <div className="content-card">
                  <h3>Related Recipes</h3>
                  <ul className="stack-list">
                    {activeRecipe.related_recipes.length > 0 ? (
                      activeRecipe.related_recipes.map((item, index) => (
                        <li key={`${item}-${index}`}>{item}</li>
                      ))
                    ) : (
                      <li>No related recipes suggested.</li>
                    )}
                  </ul>
                </div>
              </section>
            </div>
          ) : (
            <p className="empty-state">
              Start by extracting a recipe URL or choosing one from the saved
              recipe list.
            </p>
          )}
        </section>
      </section>
    </main>
  )
}

function InfoCard({
  label,
  value,
}: {
  label: string
  value?: string
}) {
  return (
    <div className="info-card">
      <span>{label}</span>
      <strong>{value || 'Unknown'}</strong>
    </div>
  )
}

function formatDate(value: string) {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }

  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function getErrorMessage(error: unknown, fallback: string) {
  if (axios.isAxiosError(error)) {
    if (error.code === 'ERR_NETWORK') {
      return `Could not reach the backend at ${API_BASE_URL}. Make sure the FastAPI server is running and accessible from the browser.`
    }

    if (error.response?.status === 500) {
      return `The backend responded with a 500 error at ${API_BASE_URL}. The API server is reachable, but something failed on the backend while processing the request.`
    }
  }

  if (
    typeof error === 'object' &&
    error !== null &&
    'response' in error &&
    typeof error.response === 'object' &&
    error.response !== null &&
    'data' in error.response &&
    typeof error.response.data === 'object' &&
    error.response.data !== null &&
    'detail' in error.response.data &&
    typeof error.response.data.detail === 'string'
  ) {
    return error.response.data.detail
  }

  if (error instanceof Error) {
    return error.message
  }

  return fallback
}

export default App
