<template>
	<Dialog
		v-model="show"
		:options="{
			size: '5xl',
		}"
	>
		<template #body>
			<div class="p-5 space-y-5">
				<div class="text-lg font-semibold text-ink-gray-9 mb-5">
					{{ __(props.title) }}
				</div>
				<div
					v-if="!editMode"
					class="flex items-center text-xs text-ink-gray-7 space-x-5"
				>
					<Switch
						size="sm"
						:label="__('Choose an existing question')"
						v-model="chooseFromExisting"
						class="!p-0"
					/>
				</div>
				<div v-if="!chooseFromExisting || editMode">
					<div>
						<label class="block text-xs text-ink-gray-5 mb-1">
							{{ __('Question') }}
						</label>
						<TextEditor
							:content="question.question"
							@change="(val) => (question.question = val)"
							:editable="true"
							:fixedMenu="true"
							editorClass="prose-sm max-w-none border-b border-x bg-surface-gray-2 rounded-b-md py-1 px-2 min-h-[7rem]"
						/>
					</div>
					<div class="grid grid-cols-2 gap-8 mt-4">
						<FormControl
							v-model="question.marks"
							:label="__('Marks')"
							type="number"
						/>
						<FormControl
							:label="__('Type')"
							v-model="question.type"
							type="select"
							:options="['Choices', 'User Input', 'Open Ended', 'Reading Block']"
							class="pb-2"
							:required="true"
						/>
					</div>
					<div
						v-if="question.type == 'Choices'"
						class="text-base font-semibold text-ink-gray-9 mb-5 mt-10"
					>
						{{ __('Options') }}
					</div>
					<div
						v-else-if="question.type == 'User Input'"
						class="text-base font-semibold text-ink-gray-9 mb-5 mt-5"
					>
						{{ __('Possibilities') }}
					</div>
					<div
						v-else-if="question.type == 'Reading Block'"
						class="text-base font-semibold text-ink-gray-9 mb-5 mt-5"
					>
						{{ __('Sub Questions') }}
					</div>
					<div
						v-if="question.type == 'Choices'"
						class="grid grid-cols-2 gap-x-8 gap-y-4"
					>
						<div v-for="n in 4" class="space-y-4 py-2">
							<FormControl
								:label="__('Option') + ' ' + n"
								v-model="question[`option_${n}`]"
								:required="n <= 2 ? true : false"
							/>
							<FormControl
								:label="__('Explanation')"
								v-model="question[`explanation_${n}`]"
							/>
							<FormControl
								:label="__('Correct Answer')"
								v-model="question[`is_correct_${n}`]"
								type="checkbox"
							/>
						</div>
					</div>
					<div
						v-else-if="question.type == 'User Input'"
						class="grid grid-cols-2 gap-x-8 gap-y-4 py-2"
					>
						<div v-for="n in 4">
							<FormControl
								:label="__('Possibility') + ' ' + n"
								v-model="question[`possibility_${n}`]"
								:required="n == 1 ? true : false"
							/>
						</div>
					</div>
					<div
						v-else-if="question.type == 'Reading Block'"
						class="space-y-4 py-2"
					>
						<div class="bg-surface-gray-1 border rounded-lg p-3">
							<div class="text-sm text-ink-gray-6">
								{{ __('Reading Block: Add reading passage above, then create sub-questions below') }}
							</div>
						</div>
						
						<!-- Sub Questions Management -->
						<div class="space-y-3">
							<div class="flex items-center justify-between">
								<span class="text-sm font-medium text-ink-gray-8">{{ __('Sub Questions') }}</span>
								<Button
									size="sm"
									variant="outline"
									@click="addSubQuestion"
								>
									{{ __('+ Add Question') }}
								</Button>
							</div>
							
							<div v-if="question.sub_questions.length === 0" class="text-center py-6 text-ink-gray-5 text-sm">
								{{ __('No sub-questions yet') }}
							</div>
							
							<div v-for="(subQ, index) in question.sub_questions" :key="index" class="border rounded-lg p-3 space-y-3">
								<div class="flex items-center justify-between">
									<span class="text-sm font-medium">{{ __('Question') }} {{ index + 1 }}</span>
									<Button
										size="sm"
										variant="ghost"
										@click="removeSubQuestion(index)"
										class="text-red-600"
									>
										{{ __('Remove') }}
									</Button>
								</div>
								
								<FormControl
									v-model="subQ.question"
									:label="__('Question Text')"
									:required="true"
								/>
								
								<div class="grid grid-cols-2 gap-3">
									<div class="space-y-1">
										<FormControl
											v-model="subQ.option_1"
											:label="__('Option 1')"
											:required="true"
										/>
										<FormControl
											v-model="subQ.is_correct_1"
											:label="__('Correct')"
											type="checkbox"
										/>
									</div>
									<div class="space-y-1">
										<FormControl
											v-model="subQ.option_2"
											:label="__('Option 2')"
											:required="true"
										/>
										<FormControl
											v-model="subQ.is_correct_2"
											:label="__('Correct')"
											type="checkbox"
										/>
									</div>
								</div>
								
								<div class="grid grid-cols-2 gap-3">
									<div class="space-y-1">
										<FormControl
											v-model="subQ.option_3"
											:label="__('Option 3')"
										/>
										<FormControl
											v-model="subQ.is_correct_3"
											:label="__('Correct')"
											type="checkbox"
										/>
									</div>
									<div class="space-y-1">
										<FormControl
											v-model="subQ.option_4"
											:label="__('Option 4')"
										/>
										<FormControl
											v-model="subQ.is_correct_4"
											:label="__('Correct')"
											type="checkbox"
										/>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
				<div v-else-if="chooseFromExisting" class="space-y-2">
					<Link
						v-model="existingQuestion.question"
						:label="__('Select a question')"
						doctype="LMS Question"
					/>
					<FormControl
						v-model="existingQuestion.marks"
						:label="__('Marks')"
						type="number"
					/>
				</div>
				<div class="flex items-center justify-end space-x-2 mt-5">
					<Button variant="solid" @click="submitQuestion()">
						{{ __('Save') }}
					</Button>
				</div>
			</div>
		</template>
	</Dialog>
</template>
<script setup>
import {
	Dialog,
	FormControl,
	TextEditor,
	createResource,
	Switch,
	Button,
	toast,
} from 'frappe-ui'
import { computed, watch, reactive, ref, inject } from 'vue'
import Link from '@/components/Controls/Link.vue'
import { useOnboarding } from 'frappe-ui/frappe'

const show = defineModel()
const quiz = defineModel('quiz')
const chooseFromExisting = ref(false)
const editMode = ref(false)
const user = inject('$user')
const { updateOnboardingStep } = useOnboarding('learning')

const existingQuestion = reactive({
	question: '',
	marks: 1,
})
const question = reactive({
	question: '',
	type: 'Choices',
	marks: 1,
	sub_questions: [],
})

const populateFields = () => {
	let fields = ['option', 'is_correct', 'explanation', 'possibility']
	let counter = 1
	fields.forEach((field) => {
		while (counter <= 4) {
			question[`${field}_${counter}`] = field === 'is_correct' ? false : null
			counter++
		}
	})
}

populateFields()

// Sub-questions management for Reading Block
const addSubQuestion = () => {
	question.sub_questions.push({
		question: '',
		option_1: '',
		option_2: '',
		option_3: '',
		option_4: '',
		is_correct_1: false,
		is_correct_2: false,
		is_correct_3: false,
		is_correct_4: false,
	})
}

const removeSubQuestion = (index) => {
	question.sub_questions.splice(index, 1)
}

const props = defineProps({
	title: {
		type: String,
		default: __('Add a new question'),
	},
	questionDetail: {
		type: [Object, null],
		required: true,
	},
})

const questionData = createResource({
	url: 'frappe.client.get',
	makeParams() {
		return {
			doctype: 'LMS Question',
			name: props.questionDetail.question,
		}
	},
	auto: false,
	onSuccess(data) {
		let counter = 1
		editMode.value = true
		Object.keys(data).forEach((key) => {
			if (Object.hasOwn(question, key)) question[key] = data[key]
		})
		while (counter <= 4) {
			question[`is_correct_${counter}`] = data[`is_correct_${counter}`]
				? true
				: false
			counter++
		}
		question.marks = props.questionDetail.marks
	},
})

watch(show, () => {
	if (show.value) {
		editMode.value = false
		if (props.questionDetail.question) questionData.fetch()
		else {
			question.question = ''
			question.marks = 1
			question.type = 'Choices'
			existingQuestion.question = ''
			existingQuestion.marks = 1
			chooseFromExisting.value = false
			populateFields()
		}

		if (props.questionDetail.marks) question.marks = props.questionDetail.marks
	}
})

const questionRow = createResource({
	url: 'frappe.client.insert',
	makeParams(values) {
		return {
			doc: {
				doctype: 'LMS Quiz Question',
				parent: quiz.value.doc.name,
				parentfield: 'questions',
				parenttype: 'LMS Quiz',
				...values,
			},
		}
	},
})

const questionCreation = createResource({
	url: 'frappe.client.insert',
	makeParams(values) {
		return {
			doc: {
				doctype: 'LMS Question',
				...question,
			},
		}
	},
})

const submitQuestion = () => {
	if (props.questionDetail?.question) updateQuestion()
	else addQuestion()
}

const addQuestion = () => {
	if (chooseFromExisting.value) {
		addQuestionRow({
			question: existingQuestion.question,
			marks: existingQuestion.marks,
		})
	} else {
		questionCreation.submit(
			{},
			{
				onSuccess(data) {
					addQuestionRow({
						question: data.name,
						marks: question.marks,
					})
				},
				onError(err) {
					toast.error(err.messages?.[0] || err)
				},
			}
		)
	}
}

const addQuestionRow = (question) => {
	questionRow.submit(
		{
			...question,
		},
		{
			onSuccess() {
				if (user.data?.is_system_manager)
					updateOnboardingStep('create_first_quiz')

				show.value = false
				toast.success(__('Question added successfully'))
				quiz.value.reload()
				show.value = false
			},
			onError(err) {
				toast.error(err.messages?.[0] || err)
				show.value = false
			},
		}
	)
}

const questionUpdate = createResource({
	url: 'frappe.client.set_value',
	auto: false,
	makeParams(values) {
		return {
			doctype: 'LMS Question',
			name: questionData.data?.name,
			fieldname: {
				...question,
			},
		}
	},
})

const marksUpdate = createResource({
	url: 'frappe.client.set_value',
	auto: false,
	makeParams(values) {
		return {
			doctype: 'LMS Quiz Question',
			name: props.questionDetail.name,
			fieldname: {
				marks: question.marks,
			},
		}
	},
})

const updateQuestion = () => {
	questionUpdate.submit(
		{},
		{
			onSuccess() {
				marksUpdate.submit(
					{},
					{
						onSuccess() {
							show.value = false
							toast.success(__('Question updated successfully'))
							quiz.value.reload()
						},
					}
				)
			},
			onError(err) {
				toast.error(err.messages?.[0] || err)
			},
		}
	)
}
</script>
<style>
input[type='radio']:checked {
	background-color: theme('colors.gray.900') !important;
	border-color: theme('colors.gray.900') !important;
	--tw-ring-color: theme('colors.gray.900') !important;
}
</style>
