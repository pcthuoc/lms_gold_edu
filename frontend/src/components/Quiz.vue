<template>
	<div v-if="quiz.data">
		<div
			class="bg-surface-blue-2 space-y-2 py-2 px-3 mb-4 rounded-md text-sm text-ink-blue-2 leading-5"
		>
			<div v-if="inVideo">
				{{ __('You will have to complete the quiz to continue the video') }}
			</div>
			<div class="leading-5">
				{{
					__('This quiz consists of {0} questions.').format(questions.length)
				}}
			</div>
			<div v-if="quiz.data?.duration" class="leading-5">
				{{
					__(
						'Please ensure that you complete all the questions in {0} minutes.'
					).format(quiz.data.duration)
				}}
			</div>
			<div v-if="quiz.data?.duration" class="leading-5">
				{{
					__(
						'If you fail to do so, the quiz will be automatically submitted when the timer ends.'
					)
				}}
			</div>
			<div v-if="quiz.data.passing_percentage" class="leading-relaxed">
				{{
					__(
						'You will have to get {0}% correct answers in order to pass the quiz.'
					).format(quiz.data.passing_percentage)
				}}
			</div>
			<div v-if="quiz.data.max_attempts" class="leading-5">
				{{
					__('You can attempt this quiz {0}.').format(
						quiz.data.max_attempts == 1
							? '1 time'
							: `${quiz.data.max_attempts} times`
					)
				}}
			</div>
			<div v-if="quiz.data.enable_negative_marking" class="leading-5">
				{{
					__(
						'If you answer incorrectly, {0} {1} will be deducted from your score for each incorrect answer.'
					).format(
						quiz.data.marks_to_cut,
						quiz.data.marks_to_cut == 1 ? 'mark' : 'marks'
					)
				}}
			</div>
		</div>

		<div v-if="quiz.data.duration" class="flex flex-col space-x-1 my-4">
			<div class="mb-2">
				<span class=""> {{ __('Time') }}: </span>
				<span class="font-semibold">
					{{ formatTimer(timer) }}
				</span>
			</div>
			<ProgressBar :progress="timerProgress" />
		</div>

		<div v-if="activeQuestion == 0">
			
			<div class="border text-center p-20 rounded-md">
				<div class="font-semibold text-lg text-ink-gray-9">
					{{ quiz.data.title }}
				</div>
				<div class="flex items-center justify-center space-x-2 mt-4">
					<Button
						v-if="
							!quiz.data.max_attempts ||
							attempts.data?.length < quiz.data.max_attempts
						"
						variant="solid"
						@click="startQuiz"
					>
						<span>
							{{ inVideo ? __('Start the Quiz') : __('Start') }}
						</span>
					</Button>
					<Button v-if="inVideo" @click="props.backToVideo()">
						{{ __('Resume Video') }}
					</Button>
				</div>
				<div
					v-if="
						quiz.data.max_attempts &&
						attempts.data?.length >= quiz.data.max_attempts
					"
					class="leading-5 text-ink-gray-7"
				>
					{{
						__(
							'You have already exceeded the maximum number of attempts allowed for this quiz.'
						)
					}}
				</div>
			</div>
		</div>
		
		<!-- Sequential Mode -->
		<div v-else-if="!quizSubmission.data && isSequentialMode">
			<div v-for="(question, qtidx) in questions">
				<div
					v-if="qtidx == activeQuestion - 1 && questionDetails.data"
					class="border rounded-md p-5"
				>
					<div class="flex justify-between">
						<div class="text-sm text-ink-gray-5">
							<span class="mr-2">
								{{ __('Question {0}').format(activeQuestion) }}:
							</span>
							<span>
								{{ getInstructions(questionDetails.data) }}
							</span>
						</div>
						<div class="text-ink-gray-9 text-sm font-semibold item-left">
							{{ question.marks }}
							{{ question.marks == 1 ? __('Mark') : __('Marks') }}
						</div>
					</div>
					<div
						class="text-ink-gray-9 font-semibold mt-2 leading-5"
						v-html="questionDetails.data.question"
					></div>
					
					<!-- Choices Question -->
					<div v-if="questionDetails.data.type == 'Choices'">
						<div v-for="index in 4" :key="index">
						<label
							v-if="questionDetails.data[`option_${index}`]"
							class="flex items-center bg-surface-gray-3 rounded-md p-3 mt-4 w-full cursor-pointer focus:border-blue-600"
						>
							<input
								v-if="!showAnswers.length && !questionDetails.data.multiple"
								type="radio"
								:name="encodeURIComponent(questionDetails.data.question)"
								class="w-3.5 h-3.5 text-ink-gray-9 focus:ring-outline-gray-modals"
								@change="markAnswer(index)"
							/>

							<input
								v-else-if="!showAnswers.length && questionDetails.data.multiple"
								type="checkbox"
								:name="encodeURIComponent(questionDetails.data.question)"
								class="w-3.5 h-3.5 text-ink-gray-9 rounded-sm focus:ring-outline-gray-modals"
								@change="markAnswer(index)"
							/>
							<div
								v-else-if="quiz.data.show_answers && showAnswers.length"
								class="w-3.5 h-3.5 flex items-center justify-center"
							>
								<CheckCircle
									v-if="showAnswers[index - 1] == 1"
									class="w-4 h-4 text-ink-green-2 mr-1"
								/>
								<MinusCircle
									v-else-if="showAnswers[index - 1] == 2"
									class="w-4 h-4 text-ink-green-2 mr-1"
								/>
								<XCircle
									v-else-if="showAnswers[index - 1] == 0"
									class="w-4 h-4 text-ink-red-3 mr-1"
								/>
								<div v-else class="w-4 h-4"></div>
							</div>
							<span
								class="ml-2"
								v-html="questionDetails.data[`option_${index}`]"
							>
							</span>
						</label>
						<div
							v-if="questionDetails.data[`explanation_${index}`]"
							class="mt-2 text-xs"
							v-show="showAnswers.length"
						>
							{{ questionDetails.data[`explanation_${index}`] }}
						</div>
					</div>
					
					<!-- Hiển thị trạng thái câu hỏi sau 4 đáp án - ✅ All-or-Nothing Logic -->
					<div v-if="showAnswers.length && questionDetails.data.type == 'Choices'" class="mt-4 flex justify-center">
					<Badge v-if="isSequentialQuestionCorrect()" :label="__('Correct')" theme="green">
							<template #prefix>
								<CheckCircle class="w-4 h-4 text-ink-green-2 mr-1" />
							</template>
						</Badge>
					<Badge v-else :label="__('Incorrect')" theme="red">
							<template #prefix>
								<XCircle class="w-4 h-4 text-ink-red-3 mr-1" />
							</template>
						</Badge>
					</div>
					</div>
					
					<div v-else-if="questionDetails.data.type == 'User Input'">
						<FormControl
							v-model="possibleAnswer"
							type="textarea"
							:disabled="showAnswers.length ? true : false"
							class="my-2"
						/>
						<div v-if="showAnswers.length">
							<!-- Logic cho mode hiển thị đáp án: showAnswers[0] là object -->
							<div v-if="quiz.data.show_answers && typeof showAnswers[0] === 'object'">
							<Badge v-if="showAnswers[0].is_correct" :label="__('Correct')" theme="green">
									<template #prefix>
										<CheckCircle class="w-4 h-4 text-ink-green-2 mr-1" />
									</template>
								</Badge>
							<Badge v-else theme="red" :label="__('Incorrect')">
									<template #prefix>
										<XCircle class="w-4 h-4 text-ink-red-3 mr-1" />
									</template>
								</Badge>
								
								<!-- Hiển thị đáp án đúng -->
								<div v-if="showAnswers[0].correct_answers && showAnswers[0].correct_answers.length" class="mt-3 p-3 bg-green-50 border border-green-200 rounded-md">
									<div class="text-sm font-medium text-green-800 mb-2">{{ __('Correct Answer(s):') }}</div>
									<div class="text-sm text-green-700">
										<div v-for="(answer, idx) in showAnswers[0].correct_answers" :key="idx" class="mb-1">
											• {{ answer }}
										</div>
									</div>
								</div>
							</div>
							
							<div v-else>
							<Badge v-if="showAnswers[0]" :label="__('Correct')" theme="green">
									<template #prefix>
										<CheckCircle class="w-4 h-4 text-ink-green-2 mr-1" />
									</template>
								</Badge>
							<Badge v-else theme="red" :label="__('Incorrect')">
									<template #prefix>
										<XCircle class="w-4 h-4 text-ink-red-3 mr-1" />
									</template>
								</Badge>
							</div>
						</div>
					</div>
					<div v-else-if="questionDetails.data.type == 'Reading Block'">
						<!-- Reading Passage -->
						<!-- <div class="bg-surface-gray-1 border rounded-lg p-4 mb-6">
							<div class="text-sm font-medium text-ink-gray-7 mb-2">
								{{ __('Reading Passage') }}
							</div>
							<div class="prose prose-sm max-w-none" v-html="questionDetails.data.question"></div>
						</div>
						 -->
						<!-- Sub Questions -->
						<div class="space-y-6" v-if="questionDetails.data.sub_questions && questionDetails.data.sub_questions.length > 0">
							<div v-for="(subQ, subIdx) in questionDetails.data.sub_questions" :key="subIdx" class="border rounded-lg p-4">
								<div class="flex justify-between items-start mb-3">
									<div class="text-sm font-medium text-ink-gray-8">
										{{ __('Question') }} {{ subIdx + 1 }}
									</div>
								<!-- ✅ Show Correct/Incorrect status for each sub-question -->
									<div v-if="showSubAnswers[subIdx]">
										<Badge 
											v-if="getSequentialSubQuestionStatus(subIdx) === 'correct'" 
											:label="__('Correct')" 
											theme="green"
										>
											<template #prefix>
												<CheckCircle class="w-4 h-4 text-ink-green-2 mr-1" />
											</template>
										</Badge>
										<Badge 
											v-else-if="getSequentialSubQuestionStatus(subIdx) === 'incorrect'" 
											:label="__('Incorrect')" 
											theme="red"
										>
											<template #prefix>
												<XCircle class="w-4 h-4 text-ink-red-3 mr-1" />
											</template>
										</Badge>
									</div>
								</div>
								
								<div class="text-ink-gray-9 font-medium mb-3">{{ subQ.question }}</div>
								
								<!-- Sub Question Options -->
								<div class="space-y-2">
									<!-- Option 1 -->
									<label v-if="subQ.option_1" class="flex items-center bg-surface-gray-3 rounded-md p-3 cursor-pointer hover:bg-surface-gray-4 transition-colors">
										<div v-if="showSubAnswers[subIdx] && (showSubAnswers[subIdx][0] === 1 || showSubAnswers[subIdx][0] === 0 || showSubAnswers[subIdx][0] === 2)" class="w-3.5 h-3.5 flex items-center justify-center">
											<CheckCircle
												v-if="showSubAnswers[subIdx][0] == 1"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<MinusCircle
												v-else-if="showSubAnswers[subIdx][0] == 2"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<XCircle
												v-else-if="showSubAnswers[subIdx][0] == 0"
												class="w-4 h-4 text-ink-red-3 mr-1"
											/>
											<div v-else class="w-4 h-4"></div>
										</div>
										<div v-else class="w-3.5 h-3.5">
											<input
												type="radio"
												:name="`sub_question_${subIdx}`"
												class="w-3.5 h-3.5 text-ink-gray-9 focus:ring-outline-gray-modals"
												@change="markSubAnswer(subIdx, 1)"
											/>
										</div>
										<span class="ml-3">{{ subQ.option_1 }}</span>
									</label>
									
									<!-- Option 2 -->
									<label v-if="subQ.option_2" class="flex items-center bg-surface-gray-3 rounded-md p-3 cursor-pointer hover:bg-surface-gray-4 transition-colors">
										<div v-if="showSubAnswers[subIdx] && (showSubAnswers[subIdx][1] === 1 || showSubAnswers[subIdx][1] === 0 || showSubAnswers[subIdx][1] === 2)" class="w-3.5 h-3.5 flex items-center justify-center">
											<CheckCircle
												v-if="showSubAnswers[subIdx][1] == 1"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<MinusCircle
												v-else-if="showSubAnswers[subIdx][1] == 2"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<XCircle
												v-else-if="showSubAnswers[subIdx][1] == 0"
												class="w-4 h-4 text-ink-red-3"
											/>
											<div v-else class="w-4 h-4"></div>
										</div>
										<div v-else class="w-3.5 h-3.5">
											<input
												type="radio"
												:name="`sub_question_${subIdx}`"
												class="w-3.5 h-3.5 text-ink-gray-9 focus:ring-outline-gray-modals"
												@change="markSubAnswer(subIdx, 2)"
											/>
										</div>
										<span class="ml-3">{{ subQ.option_2 }}</span>
									</label>
									
									<!-- Option 3 -->
									<label v-if="subQ.option_3" class="flex items-center bg-surface-gray-3 rounded-md p-3 cursor-pointer hover:bg-surface-gray-4 transition-colors">
										<div v-if="showSubAnswers[subIdx] && (showSubAnswers[subIdx][2] === 1 || showSubAnswers[subIdx][2] === 0 || showSubAnswers[subIdx][2] === 2)" class="w-3.5 h-3.5 flex items-center justify-center">
											<CheckCircle
												v-if="showSubAnswers[subIdx][2] == 1"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<MinusCircle
												v-else-if="showSubAnswers[subIdx][2] == 2"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<XCircle
												v-else-if="showSubAnswers[subIdx][2] == 0"
												class="w-4 h-4 text-ink-red-3"
											/>
											<div v-else class="w-4 h-4"></div>
										</div>
										<div v-else class="w-3.5 h-3.5">
											<input
												type="radio"
												:name="`sub_question_${subIdx}`"
												class="w-3.5 h-3.5 text-ink-gray-9 focus:ring-outline-gray-modals"
												@change="markSubAnswer(subIdx, 3)"
											/>
										</div>
										<span class="ml-3">{{ subQ.option_3 }}</span>
									</label>
									
									<!-- Option 4 -->
									<label v-if="subQ.option_4" class="flex items-center bg-surface-gray-3 rounded-md p-3 cursor-pointer hover:bg-surface-gray-4 transition-colors">
										<div v-if="showSubAnswers[subIdx] && (showSubAnswers[subIdx][3] === 1 || showSubAnswers[subIdx][3] === 0 || showSubAnswers[subIdx][3] === 2)" class="w-3.5 h-3.5 flex items-center justify-center">
											<CheckCircle
												v-if="showSubAnswers[subIdx][3] == 1"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<MinusCircle
												v-else-if="showSubAnswers[subIdx][3] == 2"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<XCircle
												v-else-if="showSubAnswers[subIdx][3] == 0"
												class="w-4 h-4 text-ink-red-3"
											/>
											<div v-else class="w-4 h-4"></div>
										</div>
										<div v-else class="w-3.5 h-3.5">
											<input
												type="radio"
												:name="`sub_question_${subIdx}`"
											class="w-3.5 h-3.5 text-ink-gray-9 focus:ring-outline-gray-modals"
											@change="markSubAnswer(subIdx, 4)"
										/>
										</div>
										<span class="ml-3">{{ subQ.option_4 }}</span>
									</label>
								</div>
							</div>
						</div>
						
						<!-- No sub-questions message -->
						<div v-else class="text-center py-8 text-ink-gray-5">
							{{ __('No sub-questions found for this Reading Block') }}
						</div>
						
						<!-- Hiển thị trạng thái Reading Block sau tất cả sub-questions -->
						<!-- ✅ Ẩn tổng kết vì đã hiển thị Badge cho từng câu con -->
						<!-- 
						<div v-if="currentQuestionResult && questionDetails.data.type == 'Reading Block'" class="mt-6 flex justify-center">
							<Badge 
								v-if="currentQuestionResult === 'correct'" 
								:label="__('All Correct')" 
								theme="green"
							>
								<template #prefix>
									<CheckCircle class="w-4 h-4 text-ink-green-2 mr-1" />
								</template>
							</Badge>
							<Badge 
								v-else-if="currentQuestionResult === 'partial'" 
								:label="__('Partially Correct')" 
								theme="yellow"
							>
								<template #prefix>
									<MinusCircle class="w-4 h-4 text-ink-yellow-2 mr-1" />
								</template>
							</Badge>
							<Badge 
								v-else-if="currentQuestionResult === 'incorrect'" 
								:label="__('All Incorrect')" 
								theme="red"
							>
								<template #prefix>
									<XCircle class="w-4 h-4 text-ink-red-3 mr-1" />
								</template>
							</Badge>
						</div>
						-->
					</div>
					<div v-else>
						<TextEditor
							class="mt-4"
							:content="possibleAnswer"
							@change="(val) => (possibleAnswer = val)"
							:editable="true"
							:fixedMenu="true"
							editorClass="prose-sm max-w-none border-b border-x bg-surface-gray-2 rounded-b-md py-1 px-2 min-h-[7rem]"
						/>
					</div>
					<div class="flex items-center justify-between mt-4">
						<div class="text-sm text-ink-gray-5">
							{{
								__('Question {0} of {1}').format(
									activeQuestion,
									questions.length
								)
							}}
						</div>
						<Button
							v-if="
								quiz.data.show_answers &&
								questionDetails.data.type != 'Open Ended' &&
								(
									(questionDetails.data.type != 'Reading Block' && !showAnswers.length) ||
									(questionDetails.data.type == 'Reading Block' && Object.keys(showSubAnswers).length === 0)
								)
							"
							@click="checkAnswer()"
						>
							<span>
								{{ __('Check') }}
							</span>
						</Button>
						<!-- Nút Check cho mode không hiển thị đáp án -->
						<Button
							v-else-if="
								!quiz.data.show_answers &&
								questionDetails.data.type != 'Open Ended' &&
								(
									(questionDetails.data.type != 'Reading Block' && showAnswers.length === 0) ||
									(questionDetails.data.type == 'Reading Block' && Object.keys(showSubAnswers).length === 0)
								)
							"
							@click="checkAnswer()"
						>
							<span>
								{{ __('Check') }}
							</span>
						</Button>
						<!-- Nút Next cho cả hai mode -->
						<Button
							v-else-if="
								activeQuestion < questions.length &&
								(
									(questionDetails.data.type != 'Reading Block' && showAnswers.length > 0) ||
									(questionDetails.data.type == 'Reading Block' && Object.keys(showSubAnswers).length > 0)
								)
							"
							@click="nextQuestion()"
						>
							<span>
								{{ __('Next') }}
							</span>
						</Button>
						<Button 
							v-else-if="activeQuestion >= questions.length"
							@click="submitQuiz()"
						>
							<span>
								{{ __('Submit') }}
							</span>
						</Button>
					</div>
				</div>
			</div>
		</div>
		
		<!-- All Questions Mode -->
		<div v-else-if="isAllQuestionsMode" class="space-y-6">
			<div class="border rounded-md p-5">
				<div class="text-lg font-semibold text-ink-gray-9 mb-4">
					{{ quiz.data.title }} - {{ __('All Questions') }}
				</div>
				
				<div class="space-y-8">
					<div v-for="(question, qtidx) in questions" :key="qtidx" class="border rounded-lg shadow-sm bg-surface-white p-6">
						<div class="flex justify-between items-start mb-4">
							<div class="flex items-center gap-3">
								<div class="text-sm text-ink-gray-6">
									<span class="font-semibold text-ink-gray-8">
										{{ __('Question {0}').format(qtidx + 1) }}
									</span>
								</div>
								<!-- Status badge for each question (except Reading Block and User Input) -->
								<div v-if="hasQuestionResult(qtidx) && allQuestionsDetails[qtidx]?.type !== 'Reading Block' && allQuestionsDetails[qtidx]?.type !== 'User Input'" class="flex items-center gap-1">
									<span v-if="getQuestionStatus(qtidx) === 'correct'" 
										class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
										<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
											<path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"></path>
										</svg>
										Correct
									</span>
									<span v-else-if="getQuestionStatus(qtidx) === 'incorrect'" 
										class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
										<svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
											<path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
										</svg>
										Incorrect
									</span>
								</div>
								
								<div v-if="allQuestionsDetails[qtidx]?.type == 'User Input' && shouldShowBadge(qtidx)" class="flex items-center gap-1">
									<Badge v-if="isAllQuestionsQuestionCorrect(qtidx)" :label="__('Correct')" theme="green">
										<template #prefix>
											<CheckCircle class="w-4 h-4 text-ink-green-2 mr-1" />
										</template>
									</Badge>
									<Badge v-else theme="red" :label="__('Incorrect')">
										<template #prefix>
											<XCircle class="w-4 h-4 text-ink-red-3 mr-1" />
										</template>
									</Badge>
								</div>
							</div>
							<div class="text-sm font-medium text-ink-blue-3 bg-surface-blue-1 px-2 py-1 rounded">
								{{ question.marks }} {{ question.marks == 1 ? __('Mark') : __('Marks') }}
							</div>
						</div>
						
						<div class="text-ink-gray-9 font-medium mb-4 leading-relaxed" v-html="question.question_detail || question.question"></div>
						
						<!-- Loading or Error State -->
						<div v-if="!allQuestionsDetails[qtidx]" class="text-center py-4 text-ink-gray-5">
							{{ __('Loading question details...') }}
						</div>
						
						<!-- Question Content -->
						<div v-else-if="allQuestionsDetails[qtidx]">
							<!-- Choices Question -->
							<div v-if="allQuestionsDetails[qtidx].type == 'Choices'" class="space-y-3">
								<div v-for="index in 4" :key="index">
									<label
										v-if="allQuestionsDetails[qtidx][`option_${index}`]"
										class="flex items-center bg-surface-gray-2 hover:bg-surface-gray-3 rounded-lg p-4 cursor-pointer transition-colors border border-transparent hover:border-ink-gray-4"
									>
										<div v-if="!hasShownAnswers" class="w-4 h-4">
											<input
												v-if="!allQuestionsDetails[qtidx].multiple"
												type="radio"
												:name="`question_${qtidx}`"
												class="w-4 h-4 text-ink-blue-3 focus:ring-ink-blue-2"
												@change="markAllQuestionsAnswer(qtidx, index)"
												:disabled="quizSubmission.data"
											/>
											<input
												v-else
												type="checkbox"
												:name="`question_${qtidx}_${index}`"
												class="w-4 h-4 text-ink-blue-3 rounded focus:ring-ink-blue-2"
												@change="markAllQuestionsAnswer(qtidx, index)"
												:disabled="quizSubmission.data"
											/>
										</div>
										<div v-else class="w-4 h-4 flex items-center justify-center">
											<!-- Show icons only if show_answers is true -->
											<CheckCircle
												v-if="quiz.data.show_answers && allShowAnswers[qtidx] && allShowAnswers[qtidx][index - 1] == 1"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<MinusCircle
												v-else-if="quiz.data.show_answers && allShowAnswers[qtidx] && allShowAnswers[qtidx][index - 1] == 2"
												class="w-4 h-4 text-ink-green-2 mr-1"
											/>
											<XCircle
												v-else-if="quiz.data.show_answers && allShowAnswers[qtidx] && allShowAnswers[qtidx][index - 1] == 0"
												class="w-4 h-4 text-ink-red-3 mr-1"
											/>
											<div v-else class="w-4 h-4"></div>
										</div>
										<span class="ml-3 text-ink-gray-9" v-html="allQuestionsDetails[qtidx][`option_${index}`]"></span>
									</label>
									<div
										v-if="allQuestionsDetails[qtidx][`explanation_${index}`] && hasShownAnswers"
										class="mt-2 text-xs text-ink-gray-6 ml-7"
									>
										{{ allQuestionsDetails[qtidx][`explanation_${index}`] }}
									</div>
								</div>
							</div>
							
							<div v-else-if="allQuestionsDetails[qtidx].type == 'User Input'" class="space-y-3">
								<FormControl
									:value="allQuestionsAnswers[qtidx]?.possibleAnswer || ''"
									type="textarea"
									:placeholder="__('Type your answer here...')"
									:disabled="hasShownAnswers"
									class="w-full"
									@input="(event) => {
										if (!allQuestionsAnswers[qtidx]) {
											allQuestionsAnswers[qtidx] = { 
												selectedOptions: [0, 0, 0, 0],
												possibleAnswer: '',
												selectedSubOptions: {}
											}
										}
										const value = event.target ? event.target.value : event
										allQuestionsAnswers[qtidx].possibleAnswer = value
									}"
								/>
								
								<!-- ✅ Show correct answers only when quiz.data.show_answers is true -->
								<div v-if="quiz.data.show_answers && allQuestionsDetails[qtidx] && hasShownAnswers" class="mt-3 p-3 bg-surface-green-1 border border-ink-green-3 rounded-md">
									<div class="text-sm font-medium text-ink-green-3 mb-2">{{ __('Possible Correct Answers:') }}</div>
									<div class="space-y-1">
										<!-- Try correct_answers from response first -->
										<div v-if="allQuestionsDetails[qtidx].correct_answers && allQuestionsDetails[qtidx].correct_answers.length > 0">
											<div v-for="answer in allQuestionsDetails[qtidx].correct_answers" :key="answer" class="text-sm text-ink-green-2">
												• {{ answer }}
											</div>
										</div>
										<!-- Fallback to possibility fields -->
										<div v-else>
											<div v-for="possibilityNum in 4" :key="possibilityNum" v-if="allQuestionsDetails[qtidx][`possibility_${possibilityNum}`]" class="text-sm text-ink-green-2">
												• {{ allQuestionsDetails[qtidx][`possibility_${possibilityNum}`] }}
											</div>
										</div>
									</div>
								</div>
							</div>
							
							<!-- Reading Block Question -->
							<div v-else-if="allQuestionsDetails[qtidx].type == 'Reading Block'" class="space-y-6">
								<div class="space-y-6" v-if="allQuestionsDetails[qtidx].sub_questions && allQuestionsDetails[qtidx].sub_questions.length > 0">
									<div v-for="(subQ, subIdx) in allQuestionsDetails[qtidx].sub_questions" :key="subIdx" class="border rounded-lg p-4">
										<div class="flex justify-between items-start mb-3">
											<div class="text-sm font-medium text-ink-gray-8">
												{{ __('Question') }} {{ subIdx + 1 }}
											</div>
											<!-- Show Correct/Incorrect status for each sub-question -->
											<div v-if="allShowSubAnswers[qtidx] && allShowSubAnswers[qtidx][subIdx]">
												<Badge 
													v-if="getSubQuestionStatus(qtidx, subIdx) === 'correct'" 
													:label="__('Correct')" 
													theme="green"
												/>
												<Badge 
													v-else-if="getSubQuestionStatus(qtidx, subIdx) === 'incorrect'" 
													:label="__('Incorrect')" 
													theme="red"
												/>
											</div>
										</div>
										
										<div class="text-ink-gray-9 font-medium mb-3">{{ subQ.question }}</div>
										
										<!-- Sub Question Options -->
										<div class="space-y-2">
											<div v-for="optIdx in 4" :key="optIdx">
												<label v-if="subQ[`option_${optIdx}`]" class="flex items-center bg-surface-gray-3 rounded-md p-3 cursor-pointer hover:bg-surface-gray-4 transition-colors">
													<!-- Show icons only if show_answers is true -->
													<div v-if="quiz.data.show_answers && allShowSubAnswers[qtidx] && allShowSubAnswers[qtidx][subIdx] && (allShowSubAnswers[qtidx][subIdx][optIdx-1] === 1 || allShowSubAnswers[qtidx][subIdx][optIdx-1] === 0 || allShowSubAnswers[qtidx][subIdx][optIdx-1] === 2)" class="w-3.5 h-3.5 flex items-center justify-center">
														<CheckCircle
															v-if="allShowSubAnswers[qtidx][subIdx][optIdx-1] == 1"
															class="w-4 h-4 text-ink-green-2 mr-1"
														/>
														<MinusCircle
															v-else-if="allShowSubAnswers[qtidx][subIdx][optIdx-1] == 2"
															class="w-4 h-4 text-ink-green-2 mr-1"
														/>
														<XCircle
															v-else-if="allShowSubAnswers[qtidx][subIdx][optIdx-1] == 0"
															class="w-4 h-4 text-ink-red-3 mr-1"
														/>
														<div v-else class="w-4 h-4"></div>
													</div>
													<div v-else class="w-3.5 h-3.5">
														<input
															type="radio"
															:name="`all_sub_question_${qtidx}_${subIdx}`"
															class="w-3.5 h-3.5 text-ink-gray-9 focus:ring-outline-gray-modals"
															@change="markAllSubAnswer(qtidx, subIdx, optIdx)"
															:disabled="quizSubmission.data"
														/>
													</div>
													<span class="ml-3">{{ subQ[`option_${optIdx}`] }}</span>
												</label>
											</div>
										</div>
									</div>
								</div>
								<div v-else>
									<div class="text-sm">{{ __('No sub-questions found for this Reading Block') }}</div>
								</div>
							</div>
						</div>
					</div>
				</div>
				
				<!-- Submit Button for All Questions Mode -->
				<div class="mt-6 flex justify-center">
					<Button 
						v-if="!hasShownAnswers && !quizSubmission.data" 
						@click="submitAllQuestions()" 
						:disabled="quizSubmission.data"
					>
						<span>
							{{ __('Submit All Answers') }}
						</span>
					</Button>
					<div v-else-if="quizSubmission.data" class="text-center">
						<Button @click="resetQuiz()" variant="outline">
							<span>
								{{ __('Try Again') }}
							</span>
						</Button>
					</div>
				</div>
				
				<!-- Score Display when quiz is submitted - moved to bottom -->
				<div v-if="quizSubmission.data" class="mt-6 p-4 bg-surface-blue-1 border border-ink-blue-3 rounded-lg">
					<div class="text-center">
						<div class="text-lg font-semibold text-ink-blue-3 mb-2">
							{{ __('Quiz Results') }}
						</div>
						<div class="text-2xl font-bold text-ink-gray-9 mb-1">
							{{ quizSubmission.data.percentage }}% 
						</div>
						<div class="text-sm text-ink-gray-6">
							{{ __('You got {0} out of {1} correct').format(quizSubmission.data.score, quizSubmission.data.score_out_of) }}
						</div>
						<div class="text-xs text-ink-gray-5 mt-2">
							{{ quizSubmission.data.score >= quiz.data.passing_percentage ? __('Passed') : __('Failed') }}
						</div>
					</div>
				</div>
			</div>
		</div>
		
		<div v-else class="border rounded-md p-20 text-center space-y-2">
			<div class="text-lg font-semibold text-ink-gray-9">
				{{ __('Quiz Summary') }}
			</div>
			<div
				v-if="quizSubmission.data.is_open_ended"
				class="leading-5 text-ink-gray-7"
			>
				{{
					__(
						"Your submission has been successfully saved. The instructor will review and grade it shortly, and you'll be notified of your final result."
					)
				}}
			</div>
			<div v-else>
				{{
					__(
						'You got {0}% correct answers with a score of {1} out of {2}'
					).format(
						Math.ceil(quizSubmission.data.percentage),
						quizSubmission.data.score,
						quizSubmission.data.score_out_of
					)
				}}
			</div>
			<div class="space-x-2">
				<Button
					@click="resetQuiz()"
					class="mt-2"
					v-if="
						!quiz.data.max_attempts ||
						attempts?.data.length < quiz.data.max_attempts
					"
				>
					<span>
						{{ __('Try Again') }}
					</span>
				</Button>
				<Button v-if="inVideo" @click="props.backToVideo()">
					{{ __('Resume Video') }}
				</Button>
			</div>
		</div>
		<div
			v-if="
				quiz.data.show_submission_history &&
				attempts?.data &&
				attempts.data.length > 0
			"
			class="mt-10"
		>
			<ListView
				:columns="getSubmissionColumns()"
				:rows="attempts?.data"
				row-key="name"
				:options="{
					selectable: false,
					showTooltip: false,
					emptyState: { title: __('No Quiz submissions found') },
				}"
			>
			</ListView>
		</div>
	</div>
</template>
<script setup>
import {
	Badge,
	Button,
	call,
	createResource,
	ListView,
	TextEditor,
	FormControl,
	toast,
} from 'frappe-ui'
import { ref, watch, reactive, inject, computed, nextTick } from 'vue'
import { CheckCircle, XCircle, MinusCircle } from 'lucide-vue-next'
import { timeAgo } from '@/utils'
import { useRouter } from 'vue-router'
import ProgressBar from '@/components/ProgressBar.vue'

const user = inject('$user')
const activeQuestion = ref(0)
const currentQuestion = ref('')
const selectedOptions = reactive([0, 0, 0, 0])
const selectedSubOptions = reactive({}) // For Reading Block sub-questions
const showAnswers = reactive([])
const showSubAnswers = reactive({}) // For Reading Block sub-answers
let questions = reactive([])
const possibleAnswer = ref(null)
const timer = ref(0)
let timerInterval = null

// All Questions mode data
const allQuestionsAnswers = reactive({})
const allQuestionsDetails = reactive({})
const allShowAnswers = reactive({})
const allShowSubAnswers = reactive({})

// Mode detection
const isSequentialMode = computed(() => {
	// Ưu tiên quiz.data.display_mode từ database
	if (quiz.data && quiz.data.display_mode) {
		return quiz.data.display_mode === 'Sequential'
	}
	// Nếu không có, dùng displayMode prop
	if (props.displayMode) {
		return props.displayMode === 'sequential'
	}
	// Default là sequential
	return true
})

const isAllQuestionsMode = computed(() => {
	// Ưu tiên quiz.data.display_mode từ database
	if (quiz.data && quiz.data.display_mode) {
		return quiz.data.display_mode === 'All Questions'
	}
	// Nếu không có, dùng displayMode prop
	if (props.displayMode) {
		return props.displayMode === 'all_questions'
	}
	// Default là false
	return false
})

const hasShownAnswers = computed(() => {
	if (isAllQuestionsMode.value) {
		// For All Questions mode, check if any answers have been shown
		const hasShowAnswers = Object.keys(allShowAnswers).length > 0
		const hasShowSubAnswers = Object.keys(allShowSubAnswers).length > 0
		return hasShowAnswers || hasShowSubAnswers
	} else {
		// For Sequential mode, use existing logic
		return quiz.data?.show_answers && (showAnswers.length > 0 || Object.keys(showSubAnswers).length > 0)
	}
})

// ✅ Function để check Badge display cho specific question (NOT computed)
const shouldShowBadge = (questionIndex) => {
	const stringKey = questionIndex.toString()
	const hasData = allShowAnswers[stringKey] !== undefined
	return hasShownAnswers.value && hasData
}

// Helper methods for question status
const hasQuestionResult = (questionIndex) => {
	if (isAllQuestionsMode.value) {
		return allShowAnswers[questionIndex] || allShowSubAnswers[questionIndex]
	} else {
		// For Sequential mode - check current question only
		return questionIndex === currentQuestion.value && (showAnswers.length > 0 || Object.keys(showSubAnswers).length > 0)
	}
}

// Check if user has answered a question (regardless of showing results)
const hasUserAnswered = (questionIndex) => {
	if (!allQuestionsAnswers[questionIndex]) return false
	
	const answer = allQuestionsAnswers[questionIndex]
	const questionType = allQuestionsDetails[questionIndex]?.type
	
	if (questionType === 'Choices') {
		return answer.selectedOptions.some(option => option === 1)
	} else if (questionType === 'User Input') {
		return answer.possibleAnswer && answer.possibleAnswer.trim() !== ''
	} else if (questionType === 'Reading Block') {
		return Object.keys(answer.selectedSubOptions).length > 0
	}
	
	return false
}

const getQuestionStatus = (questionIndex) => {
	if (!hasQuestionResult(questionIndex)) return null
	
	if (isAllQuestionsMode.value) {
		const questionDetails = allQuestionsDetails[questionIndex]
		if (!questionDetails) return null
		
		if (questionDetails.type === 'Choices') {
			const answers = allShowAnswers[questionIndex]
			if (!answers) return null
			
			// Check if any answer is correct (value 1)
			const hasCorrect = answers.some(val => val === 1)
			const hasWrong = answers.some(val => val === 0)
			
			if (hasCorrect && !hasWrong) return 'correct'
			return 'incorrect'
			
		} else if (questionDetails.type === 'Reading Block') {
			const subAnswers = allShowSubAnswers[questionIndex]
			if (!subAnswers) return null
			
			// Check all sub-questions
			let allCorrect = true
			let hasAnswered = false
			
			Object.keys(subAnswers).forEach(subIdx => {
				const subResults = subAnswers[subIdx]
				if (subResults) {
					hasAnswered = true
					const hasCorrectInSub = subResults.some(val => val === 1)
					const hasWrongInSub = subResults.some(val => val === 0)
					
					if (hasWrongInSub || !hasCorrectInSub) {
						allCorrect = false
					}
				}
			})
			
			if (!hasAnswered) return null
			return allCorrect ? 'correct' : 'incorrect'
			
		} else if (questionDetails.type === 'User Input') {
			const answers = allShowAnswers[questionIndex]
			if (!answers) return null
			
			// For input questions, check if marked correct
			// Backend may return simple value (1/0) or array [1] or [0]
			if (Array.isArray(answers)) {
				return answers[0] === 1 ? 'correct' : 'incorrect'
			} else {
				return answers === 1 ? 'correct' : 'incorrect'
			}
		}
	} else {
		// Sequential mode logic - reuse existing logic
		if (currentQuestionResult.value) {
			return currentQuestionResult.value.is_correct ? 'correct' : 'incorrect'
		}
	}
	
	return null
}

// Get status for individual sub-question in Reading Block
const getSubQuestionStatus = (questionIndex, subQuestionIndex) => {
	if (!allShowSubAnswers[questionIndex] || !allShowSubAnswers[questionIndex][subQuestionIndex]) {
		return null
	}
	
	const subResults = allShowSubAnswers[questionIndex][subQuestionIndex]
	const hasCorrect = subResults.some(val => val === 1)
	const hasWrong = subResults.some(val => val === 0)
	
	// If user got it right (has correct answer and no wrong answers)
	if (hasCorrect && !hasWrong) {
		return 'correct'
	} else if (hasWrong || !hasCorrect) {
		return 'incorrect'
	}
	
	return null
}

const props = defineProps({
	quizName: {
		type: String,
		required: true,
	},
	displayMode: {
		type: String,
		default: 'sequential', // 'sequential' or 'all_questions'
	},
	inVideo: {
		type: Boolean,
		default: false,
	},
	backToVideo: {
		type: Function,
		default: () => {},
	},
})

const quiz = createResource({
	url: 'frappe.client.get',
	makeParams(values) {
		return {
			doctype: 'LMS Quiz',
			name: props.quizName,
		}
	},
	cache: ['quiz', props.quizName],
	auto: true,
	transform(data) {
		data.duration = parseInt(data.duration)
	},
	onSuccess(data) {
		populateQuestions()
		setupTimer()
	},
})

const populateQuestions = () => {
	let data = quiz.data
	if (data.shuffle_questions) {
		questions = shuffleArray(data.questions)
		if (data.limit_questions_to) {
			questions = questions.slice(0, data.limit_questions_to)
		}
	} else {
		questions = data.questions
	}
}

const setupTimer = () => {
	if (quiz.data.duration) {
		timer.value = quiz.data.duration * 60
	}
}

const startTimer = () => {
	timerInterval = setInterval(() => {
		timer.value--
		if (timer.value == 0) {
			clearInterval(timerInterval)
			submitQuiz()
		}
	}, 1000)
}

const formatTimer = (seconds) => {
	const hrs = Math.floor(seconds / 3600)
		.toString()
		.padStart(2, '0')
	const mins = Math.floor((seconds % 3600) / 60)
		.toString()
		.padStart(2, '0')
	const secs = (seconds % 60).toString().padStart(2, '0')
	return hrs != '00' ? `${hrs}:${mins}:${secs}` : `${mins}:${secs}`
}

const timerProgress = computed(() => {
	return (timer.value / (quiz.data.duration * 60)) * 100
})

// ✅ All-or-Nothing logic for Sequential mode
const isSequentialQuestionCorrect = () => {
	if (!showAnswers.length) return false
	
	// Count different types of answers
	const correctSelected = showAnswers.filter(answer => answer === 1).length
	const wrongSelected = showAnswers.filter(answer => answer === 0).length  
	const missedCorrect = showAnswers.filter(answer => answer === 2).length
	
	// All-or-Nothing: Perfect score required
	return wrongSelected === 0 && missedCorrect === 0 && correctSelected > 0
}

// ✅ Get status for individual sub-question in Sequential mode (Reading Block)
const getSequentialSubQuestionStatus = (subQuestionIndex) => {
	if (!showSubAnswers[subQuestionIndex]) {
		return null
	}
	
	const subResults = showSubAnswers[subQuestionIndex]
	const hasCorrect = subResults.some(val => val === 1)
	const hasWrong = subResults.some(val => val === 0)
	const hasMissed = subResults.some(val => val === 2)
	
	// All-or-Nothing logic for sub-questions
	if (hasCorrect && !hasWrong && !hasMissed) {
		return 'correct'
	} else if (hasWrong || hasMissed || !hasCorrect) {
		return 'incorrect'
	}
	
	return null
}

// ✅ UNIFIED All-or-Nothing logic for All Questions mode - reuse Sequential logic!
const isAllQuestionsQuestionCorrect = (questionIndex) => {
	// ✅ Use string key consistently to match Object.keys() behavior
	const answers = allShowAnswers[questionIndex.toString()]
	
	if (!answers) {
		return false
	}
	
	// Single answer questions - simple check
	if (!Array.isArray(answers)) {
		return answers === 1
	}
	
	// ✅ Multiple choice - reuse SAME logic as Sequential mode
	const correctSelected = answers.filter(answer => answer === 1).length
	const wrongSelected = answers.filter(answer => answer === 0).length  
	const missedCorrect = answers.filter(answer => answer === 2).length
	
	// ✅ SAME All-or-Nothing logic as Sequential
	return wrongSelected === 0 && missedCorrect === 0 && correctSelected > 0
}

// Computed property để kiểm tra câu hỏi hiện tại đúng hay sai
const currentQuestionResult = computed(() => {
	if (!quiz.data.show_answers) return null
	
	if (questionDetails.data.type === 'Reading Block') {
		// Kiểm tra Reading Block result
		if (Object.keys(showSubAnswers).length === 0) return null
		
		let totalSubQuestions = 0
		let correctSubQuestions = 0
		let hasAnyAnswer = false
		
		Object.keys(showSubAnswers).forEach(subIdx => {
			const subAnswers = showSubAnswers[subIdx]
			if (subAnswers && subAnswers.some(answer => answer !== null && answer !== undefined)) {
				hasAnyAnswer = true
				totalSubQuestions++
				// Kiểm tra xem sub-question này có đúng không (có option nào = 1)
				if (subAnswers.some(answer => answer === 1)) {
					correctSubQuestions++
				}
			}
		})
		
		if (!hasAnyAnswer) return null
		
		if (correctSubQuestions === totalSubQuestions) {
			return 'correct' // Tất cả sub-questions đúng
		} else if (correctSubQuestions > 0) {
			return 'partial' // Một phần đúng
		} else {
			return 'incorrect' // Tất cả sai
		}
	} else {
		// Logic cho Choices questions
		if (!showAnswers.length) return null
		
		// Kiểm tra xem có câu trả lời nào đúng không
		const hasCorrectAnswer = showAnswers.some(answer => answer === 1)
		const hasWrongAnswer = showAnswers.some(answer => answer === 0)
		
		if (hasCorrectAnswer && !hasWrongAnswer) {
			return 'correct' // Toàn đúng
		} else if (hasCorrectAnswer && hasWrongAnswer) {
			return 'partial' // Đúng một phần (cho multiple choice)
		} else if (hasWrongAnswer) {
			return 'incorrect' // Sai
		} else {
			return 'unanswered' // Chưa trả lời
		}
	}
})

const shuffleArray = (array) => {
	for (let i = array.length - 1; i > 0; i--) {
		const j = Math.floor(Math.random() * (i + 1))
		;[array[i], array[j]] = [array[j], array[i]]
	}
	return array
}

const attempts = createResource({
	url: 'frappe.client.get_list',
	makeParams(values) {
		return {
			doctype: 'LMS Quiz Submission',
			filters: {
				member: user.data?.name,
				quiz: quiz.data?.name,
			},
			fields: [
				'name',
				'creation',
				'score',
				'score_out_of',
				'percentage',
				'passing_percentage',
			],
			order_by: 'creation desc',
		}
	},
	transform(data) {
		data.forEach((submission, index) => {
			submission.creation = timeAgo(submission.creation)
			submission.idx = index + 1
		})
	},
})

watch(
	() => quiz.data,
	() => {
		if (quiz.data) {
			populateQuestions()
		}
		if (quiz.data && quiz.data.max_attempts) {
			attempts.reload()
			resetQuiz()
		}
	}
)

const quizSubmission = createResource({
	url: 'lms.lms.doctype.lms_quiz.lms_quiz.quiz_summary',
	makeParams(values) {
		const results = localStorage.getItem(quiz.data.title)
		
		return {
			quiz: quiz.data.name,
			results: results,
		}
	},
})

const questionDetails = createResource({
	url: 'lms.lms.utils.get_question_details',
	makeParams(values) {
		return {
			question: currentQuestion.value,
		}
	},
})

watch(activeQuestion, (value) => {
	if (
		value > 0 &&
		quiz.data &&
		Array.isArray(quiz.data.questions) &&
		quiz.data.questions[value - 1]
	) {
		currentQuestion.value = quiz.data.questions[value - 1].question
		questionDetails.reload()
	}
})

watch(
	() => props.quizName,
	(newName) => {
		if (newName) {
			quiz.reload()
		}
	}
)

const startQuiz = () => {
	activeQuestion.value = 1
	localStorage.removeItem(quiz.data.title)
	if (quiz.data.duration) startTimer()
}

const markAnswer = (index) => {
	if (!questionDetails.data.multiple)
		selectedOptions.splice(0, selectedOptions.length, ...[0, 0, 0, 0])
	selectedOptions[index - 1] = selectedOptions[index - 1] ? 0 : 1
}

const markSubAnswer = (subIdx, optIdx) => {
	if (!selectedSubOptions[subIdx]) {
		selectedSubOptions[subIdx] = [0, 0, 0, 0]
	}
	// Reset all options for this sub-question (single choice)
	selectedSubOptions[subIdx] = [0, 0, 0, 0]
	selectedSubOptions[subIdx][optIdx - 1] = 1
}

const getAnswers = () => {
	let answers = []
	const type = questionDetails.data.type

	if (type == 'Choices') {
		selectedOptions.forEach((value, index) => {
			if (selectedOptions[index])
				answers.push(questionDetails.data[`option_${index + 1}`])
		})
	} else if (type == 'Reading Block') {
		// For Reading Block, collect answers for all sub-questions
		const subAnswers = []
		questionDetails.data.sub_questions.forEach((subQ, subIdx) => {
			if (selectedSubOptions[subIdx]) {
				selectedSubOptions[subIdx].forEach((value, optIdx) => {
					if (value) {
						subAnswers.push({
							sub_question_index: subIdx,
							selected_option: optIdx + 1,
							answer_text: subQ[`option_${optIdx + 1}`]
						})
					}
				})
			}
		})
		answers = subAnswers
	} else {
		answers.push(possibleAnswer.value)
	}

	return answers
}

const checkAnswer = () => {
	let answers = getAnswers()
	const type = questionDetails.data.type
	
	if (!answers.length) {
		toast.warning(__('Please select an option'))
		return
	}
	
	// Validation đặc biệt cho Reading Block - bắt buộc trả lời TẤT CẢ sub-questions
	if (type === 'Reading Block') {
		const totalSubQuestions = questionDetails.data.sub_questions?.length || 0
		const answeredSubQuestions = new Set()
		
		// Đếm số sub-questions đã được trả lời
		answers.forEach(answer => {
			answeredSubQuestions.add(answer.sub_question_index)
		})
		
		if (answeredSubQuestions.size < totalSubQuestions) {
			const unansweredCount = totalSubQuestions - answeredSubQuestions.size
			toast.warning(__('Please answer all {0} sub-questions. You have {1} unanswered questions remaining.').format(totalSubQuestions, unansweredCount))
			return
		}
	}

	createResource({
		url: 'lms.lms.doctype.lms_quiz.lms_quiz.check_answer',
		params: {
			question: currentQuestion.value,
			type: questionDetails.data.type,
			answers: JSON.stringify(answers),
		},
		auto: true,
		onSuccess(data) {
			let type = questionDetails.data.type
			if (type == 'Choices') {
				// Reset showAnswers trước khi xử lý kết quả mới
				showAnswers.length = 0
				// ✅ FIXED: Trust backend completely - no frontend logic override
				// Backend returns: 1=correct, 0=wrong, 2=missed correct answer
				for (let index = 0; index < 4; index++) {
					showAnswers[index] = data[index] !== undefined ? data[index] : undefined
				}
			} else if (type == 'Reading Block') {
				// Handle Reading Block results - convert to simple format like Choices
				if (data && data.sub_results) {
					// Clear existing sub answers
					Object.keys(showSubAnswers).forEach(key => delete showSubAnswers[key])
					
					// Get sub-questions to know correct answers
					const subQuestions = questionDetails.data.sub_questions || []
					
					// Process each sub-question result
					data.sub_results.forEach((subResult) => {
						const subIdx = subResult.sub_question_index
						
						if (!showSubAnswers[subIdx]) {
							showSubAnswers[subIdx] = [undefined, undefined, undefined, undefined]
						}
						
						const subQ = subQuestions[subIdx]
						if (subQ) {
							// Fill answers for each option (1-4)
							for (let optIdx = 1; optIdx <= 4; optIdx++) {
								const arrayIdx = optIdx - 1
								const isCorrectOption = subQ[`is_correct_${optIdx}`]
								const userSelected = subResult.selected_option === optIdx
								
								if (userSelected && subResult.is_correct) {
									// User selected this option and it's correct
									showSubAnswers[subIdx][arrayIdx] = 1
								} else if (userSelected && !subResult.is_correct) {
									// User selected this option but it's wrong
									showSubAnswers[subIdx][arrayIdx] = 0
								} else if (!userSelected && isCorrectOption) {
									// User didn't select but this is the correct answer
									showSubAnswers[subIdx][arrayIdx] = 2
								} else {
									// Not selected and not correct
									showSubAnswers[subIdx][arrayIdx] = undefined
								}
							}
						}
					})
				}
			} else {
				showAnswers.push(data)
			}
			addToLocalStorage()
			// Trong mode không hiển thị đáp án, KHÔNG tự động reset ngay
			// Để user thấy nút "Next" và tự bấm để chuyển câu
			if (!quiz.data.show_answers) {
				// Không gọi resetQuestion() ở đây nữa
				// Sẽ gọi trong nextQuestion() thay thế
			}
		},
	})
}

const addToLocalStorage = () => {
	let quizData = JSON.parse(localStorage.getItem(quiz.data.title))
	
	// ✅ For Sequential mode, store complete answer details like All Questions mode
	let selectedAnswerTexts = getAnswers() // Get selected answer texts
	let answerDetails = []
	
	if (questionDetails.data.type === 'Choices') {
		// Convert selectedOptions to answer format that includes option_index
		selectedOptions.forEach((selected, index) => {
			if (selected) {
				answerDetails.push({
					option: questionDetails.data[`option_${index + 1}`],
					option_index: index
				})
			}
		})
	} else {
		// For other types, use the text format
		answerDetails = selectedAnswerTexts
	}
	
	let questionData = {
		question_name: currentQuestion.value,
		answer: JSON.stringify(answerDetails), // Store as JSON like All Questions mode
		is_correct: [...showAnswers], // ✅ Create a copy to avoid reference issues
	}
	
	quizData ? quizData.push(questionData) : (quizData = [questionData])
	localStorage.setItem(quiz.data.title, JSON.stringify(quizData))
}

const nextQuestion = () => {
	if (!quiz.data.show_answers && questionDetails.data?.type != 'Open Ended') {
		// Mode không hiển thị đáp án
		if ((questionDetails.data.type != 'Reading Block' && showAnswers.length === 0) ||
			(questionDetails.data.type == 'Reading Block' && Object.keys(showSubAnswers).length === 0)) {
			// Chưa check → gọi checkAnswer()
			checkAnswer()
		} else {
			// Đã check → chuyển câu tiếp theo
			resetQuestion()
		}
	} else {
		if (questionDetails.data?.type == 'Open Ended') addToLocalStorage()
		resetQuestion()
	}
}

const resetQuestion = () => {
	if (activeQuestion.value == quiz.data.questions.length) {
		return
	}
	activeQuestion.value = activeQuestion.value + 1
	selectedOptions.splice(0, selectedOptions.length, ...[0, 0, 0, 0])
	showAnswers.length = 0
	possibleAnswer.value = null
}

const submitQuiz = () => {
	if (!quiz.data.show_answers) {
		if (questionDetails.data.type == 'Open Ended') addToLocalStorage()
		else checkAnswer()
		setTimeout(() => {
			createSubmission()
		}, 500)
		return
	}
	createSubmission()
}

const createSubmission = () => {
	quizSubmission.submit(
		{},
		{
			onSuccess(data) {
				markLessonProgress()
				if (quiz.data && quiz.data.max_attempts) attempts.reload()
				if (quiz.data.duration) clearInterval(timerInterval)
			},
			onError(err) {
				const errorTitle = err?.message || ''
				if (errorTitle.includes('MaximumAttemptsExceededError')) {
					const errorMessage = err.messages?.[0] || err
					toast.error(__(errorMessage))
					setTimeout(() => {
						window.location.reload()
					}, 3000)
				}
			},
		}
	)
}

const createSubmissionAsync = () => {
	return new Promise((resolve, reject) => {
		quizSubmission.submit(
			{},
			{
				onSuccess(data) {
					markLessonProgress()
					if (quiz.data && quiz.data.max_attempts) attempts.reload()
					if (quiz.data.duration) clearInterval(timerInterval)
					resolve(data)
				},
				onError(err) {
					const errorTitle = err?.message || ''
					if (errorTitle.includes('MaximumAttemptsExceededError')) {
						const errorMessage = err.messages?.[0] || err
						toast.error(__(errorMessage))
						setTimeout(() => {
							window.location.reload()
						}, 3000)
					}
					reject(err)
				},
			}
		)
	})
}

const resetQuiz = () => {
	activeQuestion.value = 0
	selectedOptions.splice(0, selectedOptions.length, ...[0, 0, 0, 0])
	showAnswers.length = 0
	Object.keys(showSubAnswers).forEach(key => delete showSubAnswers[key])
	quizSubmission.reset()
	
	// Reset All Questions mode state properly
	Object.keys(allQuestionsAnswers).forEach(key => delete allQuestionsAnswers[key])
	Object.keys(allQuestionsDetails).forEach(key => delete allQuestionsDetails[key])
	Object.keys(allShowAnswers).forEach(key => delete allShowAnswers[key])
	Object.keys(allShowSubAnswers).forEach(key => delete allShowSubAnswers[key])
	
	populateQuestions()
	setupTimer()
	
	// Reload All Questions details if in All Questions mode
	if (isAllQuestionsMode.value) {
		setTimeout(() => {
			loadAllQuestionsDetails()
		}, 100) // Small delay to ensure questions are populated first
	}
}

const getInstructions = (question) => {
	if (question.type == 'Choices')
		if (question.multiple) return __('Choose all answers that apply')
		else return __('Choose one answer')
	else return __('Type your answer')
}

// All Questions Mode Methods
const markAllQuestionsAnswer = (questionIndex, optionIndex) => {
	if (!allQuestionsAnswers[questionIndex]) {
		allQuestionsAnswers[questionIndex] = { 
			selectedOptions: [0, 0, 0, 0],
			possibleAnswer: '',
			selectedSubOptions: {}
		}
	}
	
	const questionType = allQuestionsDetails[questionIndex]?.type
	if (questionType === 'Choices') {
		if (allQuestionsDetails[questionIndex].multiple) {
			// Multiple choice - toggle checkbox
			allQuestionsAnswers[questionIndex].selectedOptions[optionIndex - 1] = 
				allQuestionsAnswers[questionIndex].selectedOptions[optionIndex - 1] ? 0 : 1
		} else {
			// Single choice - reset others
			allQuestionsAnswers[questionIndex].selectedOptions = [0, 0, 0, 0]
			allQuestionsAnswers[questionIndex].selectedOptions[optionIndex - 1] = 1
		}
	}
}

const markAllSubAnswer = (questionIndex, subQuestionIndex, optionIndex) => {
	if (!allQuestionsAnswers[questionIndex]) {
		allQuestionsAnswers[questionIndex] = {
			selectedOptions: [0, 0, 0, 0],
			possibleAnswer: '',
			selectedSubOptions: {}
		}
	}
	
	if (!allQuestionsAnswers[questionIndex].selectedSubOptions[subQuestionIndex]) {
		allQuestionsAnswers[questionIndex].selectedSubOptions[subQuestionIndex] = [0, 0, 0, 0]
	}
	
	// Reset and set new answer for radio button
	allQuestionsAnswers[questionIndex].selectedSubOptions[subQuestionIndex] = [0, 0, 0, 0]
	allQuestionsAnswers[questionIndex].selectedSubOptions[subQuestionIndex][optionIndex - 1] = 1
}

const loadAllQuestionsDetails = async () => {
	// Safety check - make sure questions array exists and has items
	if (!questions || questions.length === 0) {
		return
	}
	
	for (let i = 0; i < questions.length; i++) {
		const question = questions[i]
		
		// Initialize answer structure
		if (!allQuestionsAnswers[i]) {
			allQuestionsAnswers[i] = {
				selectedOptions: [0, 0, 0, 0],
				possibleAnswer: '',
				selectedSubOptions: {}
			}
		}
		
		// Load question details
		try {
			const response = await call('lms.lms.utils.get_question_details', {
				question: question.question
			})
			allQuestionsDetails[i] = response
		} catch (error) {
			// Error loading question
		}
	}
}

const submitAllQuestions = async () => {
	// Validate all questions are answered
	for (let i = 0; i < questions.length; i++) {
		const answer = allQuestionsAnswers[i]
		const questionType = allQuestionsDetails[i]?.type
		
		if (questionType === 'Choices') {
			const hasAnswer = answer.selectedOptions.some(opt => opt === 1)
			if (!hasAnswer) {
				toast.warning(__('Please answer question {0}').format(i + 1))
				return
			}
		} else if (questionType === 'User Input') {
			if (!answer.possibleAnswer || (typeof answer.possibleAnswer === 'string' && answer.possibleAnswer.trim() === '')) {
				toast.warning(__('Please answer question {0}').format(i + 1))
				return
			}
		} else if (questionType === 'Reading Block') {
			const subQuestions = allQuestionsDetails[i].sub_questions || []
			for (let subIdx = 0; subIdx < subQuestions.length; subIdx++) {
				const subAnswer = answer.selectedSubOptions[subIdx]
				if (!subAnswer || !subAnswer.some(opt => opt === 1)) {
					toast.warning(__('Please answer all sub-questions in question {0}').format(i + 1))
					return
				}
			}
		}
	}
	
	// ✅ FIXED: Always check answers to get correct/incorrect results
	// show_answers only controls whether to display icons, not whether to check
	for (let i = 0; i < questions.length; i++) {
		// Always check answers to get [0,1,1,1] results for correct/incorrect logic
		await checkAllQuestionAnswer(i)
		
		// Add to localStorage for final submission
		addAllQuestionToLocalStorage(i)
	}
	// Create submission to get the score
	await createSubmissionAsync()
}

// ✅ NEW: Check answer without storing UI display results (for show_answers = false)
const checkAllQuestionAnswerNoDisplay = async (questionIndex) => {
	const answer = allQuestionsAnswers[questionIndex]
	const questionDetails = allQuestionsDetails[questionIndex]
	const question = questions[questionIndex]
	
	let answers = []
	
	if (questionDetails.type === 'Choices') {
		answer.selectedOptions.forEach((option, index) => {
			if (option) {
				answers.push({
					option: questionDetails[`option_${index + 1}`],
					option_index: index,
				})
			}
		})
	} else if (questionDetails.type === 'User Input') {
		answers.push({
			answer: answer.possibleAnswer,
		})
	} else if (questionDetails.type === 'Reading Block') {
		Object.keys(answer.selectedSubOptions).forEach(subIdx => {
			const subOptions = answer.selectedSubOptions[subIdx]
			subOptions.forEach((option, optionIdx) => {
				if (option) {
					answers.push({
						sub_question_index: parseInt(subIdx),
						option: questionDetails.sub_questions[subIdx][`option_${optionIdx + 1}`],
						option_index: optionIdx,
					})
				}
			})
		})
	}
	
	try {
		// Only validate - don't store results for UI
		await call('lms.lms.doctype.lms_quiz.lms_quiz.check_answer', {
			question: question.question,
			type: questionDetails.type,
			answers: JSON.stringify(answers),
		})
		// Results will be handled by backend during final submission
	} catch (error) {
		console.error('Error checking question:', error)
	}
}

const checkAllQuestionAnswer = async (questionIndex) => {
	const answer = allQuestionsAnswers[questionIndex]
	const questionDetails = allQuestionsDetails[questionIndex]
	const question = questions[questionIndex]
	
	let answers = []
	
	if (questionDetails.type === 'Choices') {
		answer.selectedOptions.forEach((option, index) => {
			if (option) {
				answers.push({
					option: questionDetails[`option_${index + 1}`],
					option_index: index,
				})
			}
		})
	} else if (questionDetails.type === 'User Input') {
		answers.push({
			answer: answer.possibleAnswer,
		})
	} else if (questionDetails.type === 'Reading Block') {
		Object.keys(answer.selectedSubOptions).forEach(subIdx => {
			const subOptions = answer.selectedSubOptions[subIdx]
			subOptions.forEach((option, optionIdx) => {
				if (option) {
					answers.push({
						sub_question_index: parseInt(subIdx),
						option: questionDetails.sub_questions[subIdx][`option_${optionIdx + 1}`],
						option_index: optionIdx,
					})
				}
			})
		})
	}
	
	try {
		const response = await call('lms.lms.doctype.lms_quiz.lms_quiz.check_answer', {
			question: question.question,
			type: questionDetails.type,
			answers: JSON.stringify(answers),
		})
		
		if (questionDetails.type === 'Choices') {
			// ✅ FIXED: Trust backend completely for All Questions mode too
			// ✅ Force proper Vue reactivity by setting array directly to reactive object
			const processedAnswers = []
			for (let index = 0; index < 4; index++) {
				// ✅ Keep exact values from backend - don't convert 0 or null to undefined!
				processedAnswers[index] = response[index]
			}
			
			// ✅ Use string key to match Object.keys() behavior
			allShowAnswers[questionIndex.toString()] = processedAnswers
			
			// ✅ Force Vue to recognize the change
			nextTick(() => {
				// Vue reactivity update
			})
		} else if (questionDetails.type === 'User Input') {
			// Handle new User Input response format
			
			if (response && typeof response === 'object' && 'is_correct' in response) {
				// New format with correct answers
				allShowAnswers[questionIndex] = response.is_correct
				
				// Store correct answers for display
				if (!allQuestionsDetails[questionIndex].correct_answers) {
					allQuestionsDetails[questionIndex].correct_answers = response.correct_answers || []
				}
			} else {
				// Fallback for old format
				allShowAnswers[questionIndex] = response
			}
		} else if (questionDetails.type === 'Reading Block') {
			// Phải tạo response format đúng vì backend không trả sub_results cho All Questions
			allShowSubAnswers[questionIndex] = {}
			
			// Get sub questions to process results  
			const subQuestions = questionDetails.sub_questions || []
			const userSubAnswers = answer.selectedSubOptions
			
			// Process each sub-question manually
			Object.keys(userSubAnswers).forEach(subIdx => {
				const subOptions = userSubAnswers[subIdx]
				const subQ = subQuestions[parseInt(subIdx)]
				
				if (!allShowSubAnswers[questionIndex][subIdx]) {
					allShowSubAnswers[questionIndex][subIdx] = [null, null, null, null]
				}
				
				// Check each option for this sub-question
				subOptions.forEach((wasSelected, optionIdx) => {
					if (wasSelected) {
						// User selected this option
						const isCorrect = subQ[`is_correct_${optionIdx + 1}`] === 1
						allShowSubAnswers[questionIndex][subIdx][optionIdx] = isCorrect ? 1 : 0
					} else {
						// User didn't select this option, check if it was correct
						const isCorrect = subQ[`is_correct_${optionIdx + 1}`] === 1
						if (isCorrect) {
							allShowSubAnswers[questionIndex][subIdx][optionIdx] = 2 // Correct but not selected
						}
					}
				})
			})
		}
	} catch (error) {
		// Error handling for answer checking
	}
}

const addAllQuestionToLocalStorage = (questionIndex) => {
	// Safety check
	if (!questions || questionIndex >= questions.length) {
		return
	}
	
	let quizData = JSON.parse(localStorage.getItem(quiz.data.title))
	
	// Get answer data
	const answer = allQuestionsAnswers[questionIndex]
	const questionDetails = allQuestionsDetails[questionIndex]
	const question = questions[questionIndex]
	
	if (!answer || !questionDetails || !question) {
		return
	}
	
	// Prepare answer string based on question type
	let answerString = ''
	let isCorrectArray = []
	
	if (questionDetails.type === 'Choices') {
		answerString = answer.selectedOptions.join(',')
		isCorrectArray = allShowAnswers[questionIndex] || []
	} else if (questionDetails.type === 'User Input') {
		answerString = answer.possibleAnswer || ''
		isCorrectArray = allShowAnswers[questionIndex] ? [1] : [0]
	} else if (questionDetails.type === 'Reading Block') {
		// For Reading Block, create answer string from sub-questions
		const subAnswers = []
		Object.keys(answer.selectedSubOptions).forEach(subIdx => {
			const subOptions = answer.selectedSubOptions[subIdx]
			subAnswers.push(subOptions.join(','))
		})
		answerString = subAnswers.join(';')
		// For Reading Block, check if any sub-question was correct
		const hasCorrectSubAnswer = Object.keys(allShowSubAnswers[questionIndex] || {}).some(subIdx => {
			return allShowSubAnswers[questionIndex][subIdx].some(result => result === 1)
		})
		isCorrectArray = hasCorrectSubAnswer ? [1] : [0]
	}
	
	let questionData = {
		question_name: question.question,
		answer: answerString,
		is_correct: isCorrectArray.filter((answer) => {
			return answer != undefined
		}),
	}
	
	quizData ? quizData.push(questionData) : (quizData = [questionData])
	localStorage.setItem(quiz.data.title, JSON.stringify(quizData))
}

// Load all questions when in All Questions mode
watch(() => [questions.length, isAllQuestionsMode.value], () => {
	if (isAllQuestionsMode.value && questions.length > 0) {
		loadAllQuestionsDetails()
	}
}, { immediate: true })

const markLessonProgress = () => {
	let pathname = window.location.pathname.split('/')
	if (!pathname.includes('courses'))
		pathname = window.parent.location.pathname.split('/')
	if (pathname[2] != 'courses') return
	let lessonIndex = pathname.pop().split('-')

	if (lessonIndex.length == 2) {
		call('lms.lms.api.mark_lesson_progress', {
			course: pathname[3],
			chapter_number: lessonIndex[0],
			lesson_number: lessonIndex[1],
		})
	}
}

const getSubmissionColumns = () => {
	return [
		{
			label: 'No.',
			key: 'idx',
		},
		{
			label: 'Date',
			key: 'creation',
		},
		{
			label: 'Score',
			key: 'score',
			align: 'center',
		},
		{
			label: 'Score out of',
			key: 'score_out_of',
			align: 'center',
		},
		{
			label: 'Percentage',
			key: 'percentage',
			align: 'center',
		},
	]
}
</script>
<style>
p {
	line-height: 1.5rem;
}
</style>